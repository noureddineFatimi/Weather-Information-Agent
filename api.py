from quart import Quart, request
from agent import generate_response
from werkzeug.exceptions import HTTPException
from agents import ModelBehaviorError, MaxTurnsExceeded
from quart_cors import cors

app = Quart(__name__)
app = cors(app, allow_origin="*")

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
    except ModelBehaviorError:
        return {"error": "Model encountered an error"}, 500
    except MaxTurnsExceeded:
        return {"error": "Conversation too long"}, 400
    except HTTPException:
        raise 
    except Exception:
        return {"error": "Internal Server Error"}, 500