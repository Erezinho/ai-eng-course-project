from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import uuid
import time
from datetime import datetime
import asyncio
from custom_logger import logging
from agentic_nutrition_chatbot import AgentManager
from agentic_nutrition_chatbot import ModelName

app = FastAPI(title="AutoGen API Bridge", version="1.0.0")

# Enable CORS for Open WebUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI-compatible request/response models
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]

# Initialize the wrappers - simple, 2 globals... should be in some repository
autogen_wrappers = {}  # Global variable to hold the instance

async def init_wrapper():
    global autogen_wrappers
    autogen_wrappers = {
        ModelName.GPT_OSS_20B.value: await AgentManager.async_init(model=ModelName.GPT_OSS_20B),
        ModelName.QWEN3_30B_A3B.value: await AgentManager.async_init(model=ModelName.QWEN3_30B_A3B),
    }
asyncio.run(init_wrapper())

###########################################################################

@app.get("/")
async def root():
    return {"message": "AutoGen API Bridge is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    return {
        "object": "list",
        "data": [
            {
                "id": f"{ModelName.GPT_OSS_20B.value}",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "autogen"
            },
            # {
            #     "id": f"{ModelName.QWEN3_30B.value}",
            #     "object": "model",
            #     "created": int(time.time()),
            #     "owned_by": "autogen"
            # },
            {
                "id": f"{ModelName.QWEN3_30B_A3B.value}",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "autogen"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""

    # TODO - Reset the team when new Chat starts (according to the length of the history)

    # Add logging for debugging
    logging.info(f"Received request: stream={request.stream}, model={request.model}")
    logging.info(f"Messages: {[msg for msg in request.messages]}")
    
    # Set active model
    agent_wrapper = autogen_wrappers.get(request.model)
    if not agent_wrapper:
        raise HTTPException(status_code=400, detail=f"Model {request.model} not supported")

    if request.stream:
        return await stream_chat_completions(agent_wrapper, request)

    try:
        # Process through AutoGen
        response_content = await agent_wrapper.process_message(request.messages[-1].content)

        logging.info(f"Generated response: {response_content}")
        
        # Format as OpenAI response
        response = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:10]}",
            "object": "response",
            "status": "completed", #completed, failed, in_progress, cancelled, queued, incomplete
            "created": int(time.time()),
            "model": request.model,
            "stop_reason": response_content.stop_reason,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content.messages[-1].content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                #"prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
                #"completion_tokens": sum(len(msg.content.split()) for msg in response_content.messages),
                #"total_tokens": sum(len(msg.content.split()) for msg in request.messages) + sum(len(msg.content.split()) for msg in response_content.messages)
            }
        }
        
        logging.info(f"Sending response: {response}")
        return response
        
    except Exception as e:
        logging.error(f"Error in chat completion: {e}")
        error_response = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_error"
            }
        }
        return error_response

async def stream_chat_completions(agent_wrapper: AgentManager, request: ChatCompletionRequest):
    """Handle streaming chat completions"""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate_stream():
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:10]}"
        created = int(time.time())
        
        logging.info("Starting streaming response")
        
        try:
            # Send initial chunk
            initial_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",                
                "created": created,
                "model": request.model,                
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant"
                    },
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"

            async for chunk_content in agent_wrapper.process_message_stream(request.messages[-1].content):

                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": chunk_content
                        },
                        "finish_reason": None
                    }]
                }
                
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # Send final chunk
            final_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            
            logging.info("Streaming response completed")
            
        except Exception as e:
            logging.error(f"Streaming error: {e}")
            error_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "error"
                }],
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )
