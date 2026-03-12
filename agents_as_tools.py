"""
Centralized agents-as-tools pattern for the Weather Information Agent.

This module implements a modular design where specialized agents are exposed as tools
to a main orchestrator agent. Each agent is responsible for a specific weather domain
and can be reused across different contexts.

Architecture:
- SpecializedAgent: Base class for all weather agents
- CurrentWeatherAgent: Handles current conditions queries
- ForecastAgent: Handles forecast and hourly forecast queries
- AlertsAgent: Handles weather alerts queries
- ClothingAgent: Handles clothing recommendations
- OrchestratorAgent: Main agent that uses all specialized agents as tools
"""

import asyncio
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timezone
import time

from agents import Agent, function_tool
from pydantic import Field, BaseModel
from config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME, GEMINI_API_KEY, GEMINI_MODEL_NAME, GEMINI_BASE_URL
from openai import AsyncOpenAI

from agents import set_default_openai_client, set_tracing_disabled, set_default_openai_api, Runner

# Import tools
from tools import (
    get_current_weather,
    resolve_location,
    get_weather_forecast,
    get_hourly_forecast,
    get_weather_alerts,
    suggest_weather_clothing,
)

# ============================================================================
# Configuration Setup
# ============================================================================

def setup_client_and_defaults(use_gemini: bool = False):
    """Initialize OpenAI client and default settings."""
    if use_gemini:
        client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=GEMINI_API_KEY)
        model_name = GEMINI_MODEL_NAME
    else:
        client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
        model_name = OLLAMA_MODEL_NAME

    set_default_openai_client(client=client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(disabled=True)
    
    return client, model_name


# ============================================================================
# Specialized Agent Prompts
# ============================================================================

CURRENT_WEATHER_AGENT_PROMPT = """
You are a specialized weather agent that retrieves and explains current weather conditions.

Your responsibilities:
- Use the get_current_weather tool to fetch current conditions
- Use resolve_location to convert location names to coordinates if needed
- Provide clear, concise summaries of temperature, humidity, wind, and precipitation
- Format responses in a conversational, human-friendly manner
- Never expose technical error details to the user

Always use the available tools to get real data instead of relying on your training knowledge.
"""

FORECAST_AGENT_PROMPT = """
You are a specialized weather agent that retrieves and explains weather forecasts.

Your responsibilities:
- Use resolve_location to convert location names to coordinates if needed
- Use get_weather_forecast for daily forecasts (1-16 days)
- Use get_hourly_forecast for hourly forecasts or specific time periods
- Interpret time expressions:
  - "early morning" → 03:00, 04:00, 05:00 GMT
  - "this morning" → 06:00, 07:00, 08:00 GMT
  - "this afternoon" → 12:00, 13:00, 14:00 GMT
  - "this evening" → 18:00, 19:00, 20:00 GMT
  - "tonight" / "this night" → 21:00, 22:00, 23:00 GMT
  - "midnight" → 00:00 GMT

Current UTC time: {current_utc_time} GMT (GMT+0)

Provide summaries first, then detailed information if relevant.
Always use tools to fetch real data.
"""

ALERTS_AGENT_PROMPT = """
You are a specialized weather agent that retrieves and explains weather alerts.

Your responsibilities:
- Use resolve_location to convert location names to coordinates if needed
- Use get_weather_alerts to fetch active weather warnings and alerts
- Summarize alerts clearly, highlighting severity and urgency
- If no alerts exist, explicitly inform the user
- Prioritize severe alerts in your response
- Always use tools to fetch real data

Format alerts in an easy-to-understand manner.
"""

CLOTHING_AGENT_PROMPT = """
You are a specialized weather agent that provides clothing recommendations.

Your responsibilities:
- Use resolve_location to convert location names to coordinates if needed
- Use get_current_weather to fetch current conditions
- Use suggest_weather_clothing to get tailored recommendations
- Consider the activity type and weather conditions
- Provide practical, friendly clothing suggestions
- Always use tools to fetch real data

Be conversational and helpful in your recommendations.
"""

ORCHESTRATOR_AGENT_PROMPT = """
You are the main Weather Information Assistant. Your role is to intelligently route user queries 
to specialized agents that handle different aspects of weather information.

Available specialized agents:
- current_weather_agent: Get current weather conditions for a location
- forecast_agent: Get weather forecasts (daily or hourly) and interpret time expressions
- alerts_agent: Get active weather alerts and warnings for a location
- clothing_agent: Get clothing recommendations based on current weather

Your responsibilities:
1. Analyze the user's query to understand what type of weather information they need
2. Determine which specialized agent(s) to use
3. Delegate to the appropriate agent(s)
4. Synthesize the results into a coherent, helpful response
5. Be conversational and friendly

Guidelines:
- Always process location queries through location_agent first if a location name is given
- For current conditions, use current_weather_agent
- For forecasts or time-based queries, use forecast_agent
- For warnings or safety-related queries, use alerts_agent
- For outfit/activity queries, use clothing_agent
- You may need multiple agents for complex queries
- If a query is not weather-related, politely explain you only handle weather queries

Current UTC time: {current_utc_time} GMT (GMT+0)

Be helpful, accurate, and always use the specialized agents to get real data.
"""


# ============================================================================
# Tool Result Models
# ============================================================================

class AgentToolResult(BaseModel):
    """Result returned by an agent-as-tool."""
    agent_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float


# ============================================================================
# Specialized Agent Classes
# ============================================================================

class SpecializedAgent:
    """Base class for all specialized weather agents."""
    
    def __init__(self, name: str, model_name: str, client: AsyncOpenAI, system_prompt: str=None):
        self.name = name
        self.model_name = model_name
        self.client = client
        self.system_prompt = system_prompt
        self.agent = None
    
    async def initialize(self):
        """Initialize the agent with its tools."""
        raise NotImplementedError
    
    async def execute(self, user_input: str, system_prompt: str = None) -> str:
        """Execute the agent with the given user input."""
        if self.agent is None:
            await self.initialize()
        
        start_time = time.perf_counter()
        
        try: 
            messages:list[dict[str, str]]=[]

            if system_prompt is not None: 
                messages = [
                {"role": "system", "content": system_prompt}
                ]
            
            messages.append({"role": "user", "content": user_input})

            response = await Runner.run(self.agent, input=messages)
            result = str(response.final_output)
            execution_time = time.perf_counter() - start_time
            
            print(f"[{self.name}] Execution time: {execution_time:.2f}s")
            
            return result
        
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            print(f"[{self.name}] Error: {str(e)}")
            return f"Error in {self.name}: {str(e)}"


class CurrentWeatherAgent(SpecializedAgent):
    """Agent specialized in current weather conditions."""
    
    def __init__(self, model_name: str, client: AsyncOpenAI):
        super().__init__(
            name="CurrentWeatherAgent",
            model_name=model_name,
            client=client,
            system_prompt=CURRENT_WEATHER_AGENT_PROMPT
        )
    
    async def initialize(self):
        """Initialize with current weather tools."""
        self.agent = Agent(
            name=self.name,
            model=self.model_name,
            tools=[get_current_weather, resolve_location],
            instructions=self.system_prompt
        )


class ForecastAgent(SpecializedAgent):
    """Agent specialized in weather forecasts (daily and hourly)."""
    
    def __init__(self, model_name: str, client: AsyncOpenAI):
        super().__init__(
            name="ForecastAgent",
            model_name=model_name,
            client=client
        )
    
    async def initialize(self):
        """Initialize with forecast tools."""
        self.agent = Agent(
            name=self.name,
            model=self.model_name,
            tools=[
                get_weather_forecast,
                get_hourly_forecast,
                resolve_location
            ]
        )


class AlertsAgent(SpecializedAgent):
    """Agent specialized in weather alerts and warnings."""
    
    def __init__(self, model_name: str, client: AsyncOpenAI):
        super().__init__(
            name="AlertsAgent",
            model_name=model_name,
            client=client,
            system_prompt=ALERTS_AGENT_PROMPT
        )
    
    async def initialize(self):
        """Initialize with alerts tools."""
        self.agent = Agent(
            name=self.name,
            model=self.model_name,
            tools=[get_weather_alerts, resolve_location],
            instructions=self.system_prompt
        )


class ClothingAgent(SpecializedAgent):
    """Agent specialized in clothing recommendations."""
    
    def __init__(self, model_name: str, client: AsyncOpenAI):
        super().__init__(
            name="ClothingAgent",
            model_name=model_name,
            client=client,
            system_prompt=CLOTHING_AGENT_PROMPT
        )
    
    async def initialize(self):
        """Initialize with clothing recommendation tools."""
        self.agent = Agent(
            name=self.name,
            model=self.model_name,
            tools=[
                get_current_weather,
                resolve_location,
                suggest_weather_clothing
            ],
            instructions=self.system_prompt
        )

# ============================================================================
# Agents Registry
# ============================================================================

class AgentsRegistry:
    """Registry and factory for specialized agents."""
    
    def __init__(self, model_name: str, client: AsyncOpenAI):
        self.model_name = model_name
        self.client = client
        self._agents: Dict[str, SpecializedAgent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Create all specialized agents."""
        self._agents = {
            "current_weather": CurrentWeatherAgent(self.model_name, self.client),
            "forecast": ForecastAgent(self.model_name, self.client),
            "alerts": AlertsAgent(self.model_name, self.client),
            "clothing": ClothingAgent(self.model_name, self.client),
        }
    
    def get_agent(self, agent_name: str) -> Optional[SpecializedAgent]:
        """Get a specific agent by name."""
        return self._agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all available agent names."""
        return list(self._agents.keys())
    
    async def execute_agent(
        self,
        agent_name: str,
        user_input: str,
        system_prompt: str=None
    ) -> AgentToolResult:
        """Execute a specific agent and return structured result."""
        start_time = time.perf_counter()
        
        agent = self.get_agent(agent_name)
        if not agent:
            return AgentToolResult(
                agent_name=agent_name,
                success=False,
                result=None,
                error=f"Agent '{agent_name}' not found. Available: {self.list_agents()}",
                execution_time=0
            )
        
        try:
            result = await agent.execute(user_input, system_prompt)
            execution_time = time.perf_counter() - start_time
            
            return AgentToolResult(
                agent_name=agent_name,
                success=True,
                result=result,
                error=None,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            return AgentToolResult(
                agent_name=agent_name,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )


# ============================================================================
# Orchestrator Agent
# ============================================================================

class OrchestratorAgent:
    """Main orchestrator that uses specialized agents as tools."""
    
    def __init__(self, model_name: str = None, client: AsyncOpenAI = None):
        if client is None or model_name is None:
            client, model_name = setup_client_and_defaults()
        self.name="OrchestratorAgent"
        self.client = client
        self.model_name = model_name
        self.registry = AgentsRegistry(model_name, client)
        self.agent = None
        self.conversation_history: List[Dict] = []
    
    async def initialize(self):
        """Initialize the orchestrator with agent tools."""
        
        @function_tool
        async def use_current_weather_agent(query: str = Field(description="Weather query for current conditions")) -> AgentToolResult:
            """Use the specialized current weather agent."""
            result = await self.registry.execute_agent("current_weather", query)
            return result
        
        @function_tool
        async def use_forecast_agent(query: str = Field(description="Weather query for forecasts")) -> AgentToolResult:
            """Use the specialized forecast agent."""
            result = await self.registry.execute_agent("forecast", query, FORECAST_AGENT_PROMPT.format(current_utc_time=datetime.now(timezone.utc).strftime("%H:%M:%S")
            ))
            return result
        
        @function_tool
        async def use_alerts_agent(query: str = Field(description="Weather query for alerts")) -> AgentToolResult:
            """Use the specialized alerts agent."""
            result = await self.registry.execute_agent("alerts", query)
            return result
        
        @function_tool
        async def use_clothing_agent(query: str = Field(description="Weather query for clothing recommendations")) -> AgentToolResult:
            """Use the specialized clothing agent."""
            result = await self.registry.execute_agent("clothing", query)
            return result
        
        self.agent = Agent(
            name=self.name,
            model=self.model_name,
            tools=[
                use_current_weather_agent,
                use_forecast_agent,
                use_alerts_agent,
                use_clothing_agent,
            ]
        )
    
    async def query(self, user_input: str) -> str:
        """Process a user query through the orchestrator."""
        if self.agent is None:
            await self.initialize()
        
        system_prompt=ORCHESTRATOR_AGENT_PROMPT.format(
        current_utc_time=datetime.now(timezone.utc).strftime("%H:%M:%S")
    )

        start_time = time.perf_counter()
        
        self.conversation_history.append({"role": "system", "content": system_prompt})

        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        try:
            # Get response from orchestrator
            result= await Runner.run(self.agent, input=self.conversation_history)
            response = str(result.final_output)
            execution_time = time.perf_counter() - start_time
            
            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            print(f"[Orchestrator] Query processed in {execution_time:.2f}s")
            
            return response
        
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def get_agent(self, agent_name: str) -> Optional[SpecializedAgent]:
        """Get a specific specialized agent."""
        return self.registry.get_agent(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all available specialized agents."""
        return self.registry.list_agents()
    
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []


# ============================================================================
# Factory Functions
# ============================================================================

async def create_orchestrator(use_gemini: bool = False) -> OrchestratorAgent:
    """
    Create and initialize an orchestrator agent.
    
    Args:
        use_gemini: Whether to use Gemini API (default: False for Ollama)
    
    Returns:
        Initialized OrchestratorAgent
    """
    client, model_name = setup_client_and_defaults(use_gemini=use_gemini)
    
    orchestrator = OrchestratorAgent(model_name=model_name, client=client)
    await orchestrator.initialize()
    
    return orchestrator


async def create_specialized_agent(
    agent_type: Literal["current_weather", "forecast", "alerts", "clothing", "location"],
    use_gemini: bool = False
) -> SpecializedAgent:
    """
    Create and initialize a specific specialized agent.
    
    Args:
        agent_type: Type of agent to create
        use_gemini: Whether to use Gemini API (default: False for Ollama)
    
    Returns:
        Initialized specialized agent
    """
    client, model_name = setup_client_and_defaults(use_gemini=use_gemini)
    
    agents_map = {
        "current_weather": CurrentWeatherAgent,
        "forecast": ForecastAgent,
        "alerts": AlertsAgent,
        "clothing": ClothingAgent,
    }
    
    agent_class = agents_map.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(agents_map.keys())}")
    
    agent = agent_class(model_name, client)
    await agent.initialize()
    return agent


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    
    async def main():
        """Example usage of the agents-as-tools pattern."""
        
        print("=" * 80)
        print("Weather Information Agent - Agents-as-Tools Pattern")
        print("=" * 80)
        
        # Create orchestrator
        print("\n[*] Initializing orchestrator agent...")
        orchestrator = await create_orchestrator(use_gemini=False)
        print(f"[✓] Orchestrator initialized")
        print(f"[✓] Available agents: {orchestrator.list_agents()}")
        
        # Example queries
        queries = [
            "What's the current weather in Paris?",
            "What will the weather be like this afternoon in London?",
            "Are there any weather alerts for New York?",
            "What should I wear for a hike tomorrow in Denver?",
        ]

        others_queries = [
            "What's the current weather in Paris?",
            "And for tomorrow?"
        ]
        
        for query in others_queries:
            print(f"\n{'─' * 80}")
            print(f"Query: {query}")
            print(f"{'─' * 80}")
            
            response = await orchestrator.query(query)
            print(f"Response:\n{response}")
            
            # Limit to first query for demo
            break
    
    # Run example
    asyncio.run(main())
