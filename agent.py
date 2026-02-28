from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, set_default_openai_api, ModelBehaviorError, MaxTurnsExceeded
from config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME
from openai import AsyncOpenAI
import asyncio
from tools import get_current_weather, resolve_location, get_weather_forecast

client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

async def main():
    try:
        agent = Agent( name="Assistant", instructions="You are a gentle weather information agent that provides informations about weather conditions", model=OLLAMA_MODEL_NAME, tools=[resolve_location, get_current_weather, get_weather_forecast])
        result = await Runner.run(agent, "It's will raining tomorrow in Casablanca?")
        print(result.final_output)
    except ModelBehaviorError:
        print("Model encountered an error")
    except MaxTurnsExceeded:
        print("Conversation too long" )
    
if __name__ == "__main__":
    asyncio.run(main())