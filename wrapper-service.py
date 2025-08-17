# server.py
import uuid, time
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
#from agent import run_agent  # import your AutoGen runner

app = FastAPI()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7

@app.get("/v1/models")
async def list_models():
    # Dummy list of models. 
    # Practically the wrapper name
    return {
        "object": "list",
        "data": [
            {
                "id": "AI Agents Wrapper",
                "object": "model",
                "created": 0,
                "owned_by": "local",
                "permission": [],
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    # Get the last user message from messages list
    user_input = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
    
    reply = "Walla Yofi" #run_agent(user_input)

    return {
        "id": f"ai-engineering-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(user_input.split()),  # fake count
            "completion_tokens": len(reply.split()),
            "total_tokens": len(user_input.split()) + len(reply.split())
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
