from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, set_default_openai_api, ModelBehaviorError, MaxTurnsExceeded
from config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME
from openai import AsyncOpenAI
import asyncio
from tools import get_current_weather, resolve_location, get_weather_forecast, get_hourly_forecast,get_weather_alerts

client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

async def main():
    try:
        agent = Agent( name="Assistant", instructions="""
        You are a friendly and natural weather assistant.
            - Answer directly and clearly.
            - Be conversational and human-like.
            - Avoid overly technical formatting.
            - Summarize the important information first.
            - Only include relevant details.
            - If the user asks a yes/no question, answer it first before giving details.   
        """, model=OLLAMA_MODEL_NAME, tools=[get_weather_alerts,get_current_weather, resolve_location, get_weather_forecast, get_hourly_forecast,])
        result = await Runner.run(agent, "It's will raining today in Casablanca ?")
        print(result.final_output)
    except ModelBehaviorError:
        print("Model encountered an error")
    except MaxTurnsExceeded:
        print("Conversation too long" )
    
if __name__ == "__main__":
    asyncio.run(main())