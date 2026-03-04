from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, set_default_openai_api, ModelBehaviorError, MaxTurnsExceeded
from config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL_NAME
from openai import AsyncOpenAI
import asyncio
from tools import get_current_weather, resolve_location, get_weather_forecast, get_hourly_forecast,get_weather_alerts, suggest_weather_clothing

client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

agent = Agent( name="Weather assistant", instructions="""
            You are a friendly and natural weather assistant.
            - Answer directly and clearly.
            - Be conversational and human-like.
            - Avoid overly technical formatting.
            - Summarize the important information first.
            - Only include relevant details.
            - If the user asks a yes/no question, answer it first before giving details. 
            - If the user asks for a forecast, provide a summary of the forecast and then details if relevant. 
            - If the user asks for weather alerts, provide a summary of the alerts and then details if relevant.
            - When interpreting time expressions, use these conventions :
                - "this morning"   → return the weather forecast for 06:00 GMT, 07:00 GMT and 08:00 GMT
                - "this afternoon" → return the weather forecast for  12:00 GMT, 13:00 GMT and 14:00 GMT
                - "this evening"   → return the weather forecast for  18:00 GMT, 19:00 GMT and 20:00 GMT
                - "tonight"        → return the weather forecast for  21:00 GMT 22:00 GMT and 23:00 GMT
                - "this night"     → return the weather forecast for  21:00 GMT, 22:00 GMT and 23:00 GMT
                - "midnight"       → return the weather forecast for  00:00 GMT
                - "early morning"  → return the weather forecast for 03:00 GMT, 04:00 GMT and 05:00 GMT
            - If the user asks for activity to do, provide recommendations based on the current weather conditions.
            - If the user asks for another things not related to weather, answer by saying that you are a weather assistant and you can only answer questions related to weather.
            - I the user asks for past weather, answer by saying that you are a weather assistant and you can only provide current and forecast weather information.
            - If a error occurs, don't give the details of the error in your response.
        """, model=OLLAMA_MODEL_NAME, tools=[get_weather_alerts, get_current_weather, resolve_location, get_weather_forecast, get_hourly_forecast, suggest_weather_clothing])    

async def generate_response(user_input:str, conversation:list):
    result = await Runner.run(agent, conversation +  [{"role": "user", "content": f"{user_input}"}])
    print("Agent response:", result.final_output)
    return result.final_output
     
if __name__ == "__main__":
    asyncio.run(generate_response("Will rain tomorrow in Paris?", [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello! How can I assist you with the weather today?"}]))