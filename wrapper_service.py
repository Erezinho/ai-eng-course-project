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

# Your AutoGen system wrapper Dummy
# class AutoGenWrapperDummy:
#     def __init__(self):
#         # Initialize your AutoGen system here
#         # self.agent_system = YourAgentSystem()
#         pass
    
#     async def process_message(self, messages: List[Message]) -> str:
#         """
#         Process messages through your AutoGen system
#         Convert OpenAI format to your system's format and back
#         """
#         try:
#             # Extract the latest user message
#             user_message = messages[-1].content if messages else ""
            
#             # Convert message history to your AutoGen system format
#             conversation_history = []
#             for msg in messages[:-1]:  # All except the last message
#                 conversation_history.append({
#                     "role": msg.role,
#                     "content": msg.content
#                 })
            
#             # TODO: Replace this with your actual AutoGen system call
#             # Example:
#             # response = await self.agent_system.process(
#             #     message=user_message,
#             #     history=conversation_history,
#             #     model=model
#             # )
            
#             # Placeholder response - replace with your AutoGen system
#             response = f"AutoGen processed: {user_message}"
            
#             return response
            
#         except Exception as e:
#             logging.error(f"Error processing message: {e}")
#             raise HTTPException(status_code=500, detail=str(e))

#     async def process_message_stream(self, messages: List[Message]):
#         """
#         Process messages through your AutoGen system with streaming
#         """
#         try:
#             # Get the response from your AutoGen system
#             response = await self.process_message(messages)
            
#             # Simulate streaming by yielding chunks
#             # Replace this with actual streaming from your AutoGen system if supported
#             words = response.split()
#             for i, word in enumerate(words):
#                 chunk_content = word + " " if i < len(words) - 1 else word
#                 yield chunk_content
#                 await asyncio.sleep(0.05)  # Small delay for streaming effect
                
#         except Exception as e:
#             logging.error(f"Error in streaming: {e}")
#             yield f"Error: {str(e)}"

###########################################################################

# Initialize the wrapper
#use_dummy = False
autogen_wrapper = None  # Global variable to hold the instance

async def init_wrapper():
    global autogen_wrapper
    autogen_wrapper = await AgentManager.async_init()

# if use_dummy:
#     autogen_wrapper = AutoGenWrapperDummy()
# else:
#     # Run the async initialization before the app starts
#     asyncio.run(init_wrapper())

asyncio.run(init_wrapper())

###########################################################################

@app.get("/")
async def root():
    return {"message": "AutoGen API Bridge is running"}

@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    return {
        "object": "list",
        "data": [
            {
                "id": "autogen-system",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "autogen"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    
    # Add logging for debugging
    logging.info(f"Received request: stream={request.stream}, model={request.model}")
    logging.info(f"Messages: {[msg for msg in request.messages]}")
    
    if request.stream:
        return await stream_chat_completions(request)

    try:
        # Process through AutoGen
        response_content = await autogen_wrapper.process_message(request.messages[-1].content)

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
                "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
                "completion_tokens": sum(len(msg.content.split()) for msg in response_content.messages),
                "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + sum(len(msg.content.split()) for msg in response_content.messages)
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

async def stream_chat_completions(request: ChatCompletionRequest):
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
            
            async for chunk_content in autogen_wrapper.process_message_stream(request.messages[-1].content):

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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

# # server.py
# import json
# import uuid, time
# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel
# import uvicorn
# from agentic_nutrition_chatbot import AgentManager
# from contextlib import asynccontextmanager
# from custom_logger import logger

# class ChatMessage(BaseModel):
#     role: str
#     content: str

# class ChatRequest(BaseModel):
#     model: str
#     messages: list[ChatMessage]
#     temperature: float = 0.7

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup code here
#     app.state.agent_manager = await AgentManager.async_init()
#     logger.info("🚀 Agentic system initialized and ready.")

#     yield
#     # Shutdown logic
#     await app.state.agent_manager.shutdown()
#     logger.info("🛑 Agentic system shutting down...")
#     #sessions.clear()

# app = FastAPI(lifespan=lifespan)

# @app.get("/v1/models")
# async def list_models():
#     # Dummy list of models. 
#     # Practically the wrapper name
#     return {
#         "object": "list",
#         "data": [
#             {
#                 "id": "AI Agents Wrapper",
#                 "object": "model",
#                 "created": 0,
#                 "owned_by": "local",
#                 "permission": [],
#             }
#         ]
#     }

# @app.post("/v1/chat/completions")
# async def chat_completions(request: ChatRequest):
#     # Get the last user message from messages list
#     user_input = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
    
#     reply = await app.state.agent_manager.process_message(user_input)  # This may need to be async if your agent is async
    
#     #reply = "Walla Yofi" #run_agent(user_input)

#     if request.stream:
#         return StreamingResponse(stream_reply(reply, request.model), media_type="text/event-stream")
#     else:
#         return {
#             "id": f"ai-engineering-{uuid.uuid4()}",
#             "object": "chat.completion",
#             "created": int(time.time()),
#             "model": request.model,
#             "choices": [{
#                 "index": 0,
#                 "message": {"role": "assistant", "content": reply},
#                 "finish_reason": "stop"
#             }],
#             "usage": {
#                 "prompt_tokens": len(user_input.split()),  # fake count
#                 "completion_tokens": len(reply.split()),
#                 "total_tokens": len(user_input.split()) + len(reply.split())
#             }
#         }
    
# def stream_reply(reply: str, model: str):
#     # Simulate token-by-token output
#     for token in reply.split():
#         chunk = {
#             "id": "chatcmpl-stream",
#             "object": "chat.completion.chunk",
#             "created": int(time.time()),
#             "model": model,
#             "choices": [{
#                 "delta": {"content": token + " "},
#                 "index": 0,
#                 "finish_reason": None
#             }]
#         }
#         yield f"data: {json.dumps(chunk)}\n\n"
#         time.sleep(0.05)  # small delay for realism

#     # Final message to signal end
#     yield "data: [DONE]\n\n"

# if __name__ == "__main__":
#     #logger = setup_colored_logging()
#     uvicorn.run(app, host="0.0.0.0", port=8000)

