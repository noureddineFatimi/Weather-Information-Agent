from quart import Quart, request
from agent import generate_response, generate_stream_response, generate_stream_response_by_model
from werkzeug.exceptions import HTTPException
from agents import ModelBehaviorError, MaxTurnsExceeded
from openai import APIConnectionError
from quart_cors import cors
from quart import Response

app = Quart(__name__)
app = cors(app, allow_origin="*")

@app.route("/v1/chat", methods=["POST"])
async def generate_chat_response():
    try:
        data = await request.get_json()
        if not data:
            return {"error": "Request must contain JSON body"}, 400
        user_input = data.get("user_input")
        conversation = data.get("conversation")
        model = data.get("model")
        if user_input==None or conversation==None or model==None:
            return {"error": "Keys 'user_input', 'model' and 'conversation' are required"}, 400
        return Response(generate_stream_response_by_model(user_input=user_input, conversation=conversation, model=model), content_type="text/plain")
    except Exception:
        return {"error": "Internal Server Error"}, 500

@app.route("/v1/api/agent", methods=["POST"])
async def generate_agent_response():
    try:
        data = await request.get_json()
        if not data:
            return {"error": "Request must contain JSON body"}, 400
        user_input = data.get("user_input")
        conversation = data.get("conversation")
        if user_input==None or conversation==None:
            return {"error": "Keys 'user_input' and 'conversation' are required"}, 400
        agent_response = await generate_response(
            user_input=user_input,
            conversation=conversation
        )
        return {"response": agent_response}, 200
    except APIConnectionError:
        return {"error": "Network error"}, 500
    except ModelBehaviorError:
        return {"error": "Model encountered an error"}, 500
    except MaxTurnsExceeded:
        return {"error": "Conversation too long"}, 400
    except HTTPException:
        raise 
    except Exception:
        return {"error": "Internal Server Error"}, 500