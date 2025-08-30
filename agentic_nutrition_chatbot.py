# Another magic function to write the code to a file

import asyncio
from email.mime import message
import json
from urllib import response
#from dotenv import load_dotenv
#from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.base import TaskResult
from autogen_core.models import ModelFamily #, ModelInfo
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient 
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent 
from autogen_agentchat.conditions import TextMentionTermination 
from autogen_agentchat.teams import RoundRobinGroupChat 
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.ui import Console 
from markdown_streamer import MarkdownStreamer
from custom_logger import logger
from enum import Enum
import textwrap

class ModelName(str, Enum):
    GPT_OSS_20B = "Agentic-System-gpt-oss:20b"
    #QWEN3_30B = "Agentic-System-qwen3:30b"
    QWEN3_30B_A3B = "Agentic-System-qwen3:30b-a3b"

class AgentManager:
    def __init__(self, model: ModelName, mcp_tools: list[str] = None):
        if mcp_tools is None:
            raise TypeError("mcp_tools is a required argument")

        self.markdown_streamer = MarkdownStreamer()
        
        self.model_client = self.create_model_client(model)
        logger.info(f"Using model client: {self.model_client.__class__.__name__}")

        self.end_term = "WallakAtaSoChen"  # Termination condition for the user input
        #logger.info("Starting Food chatbot based on AutoGen Agents!")

        # try:
        # Assistant Agent
        system_message_template=textwrap.dedent(f"""Your name is 'Nutrition Assistant'.
                                        You are a helpful assistant that answers questions about Meals, Food and Nutrition only.
                                        You are supplied with few tools that you must use in order to answer the user's questions.
                                        Inform the user about the tools you have accessed.
                                        When you have a suggestion for the user, output it in Markdown format.

                                        If you don't know the answer based on the tools, tell it to user, never generate an answer about
                                        Meals, Food and Nutrition without using the tools (i.e. do not invent answers not based on the tools).
                                        
                                        In addition any out of context question should be rejected for example "What is the capital of France?" or
                                        "How does a car engine work?" etc. Again, only Meals, Food and Nutrition related questions.
                                        One exception - you can tell the user which LLM you are on first greeting / interaction or if asked.
                                        
                                        End your response with the word '{self.end_term}'.
                                        If you are a Reasoning/Thinking model or use Chain of Thought,
                                        return your thinking but in one block of text, do NOT output it token by token."""
                                        #/no_think"""
        )

        self.assistant = AssistantAgent(name="assistant",
                                        model_client=self.model_client,
                                        tools=mcp_tools,
                                        model_client_stream=True,  # Enable streaming responses
                                        reflect_on_tool_use=True,  # Enable reflection on tool use
                                        system_message=system_message_template)
        logger.info("AssistantAgent created")

        # User Proxy Agent
        self.user_proxy = UserProxyAgent(name="user_proxy",
                                    input_func=self.user_input_func) 
                                    #input_func=input)  # Use input() to get user input from console.
        logger.info("UserProxyAgent created")
        

        # Termination condition which will end the conversation when the user says "quit".
        # May need also to limit number of iterations... 
        termination = TextMentionTermination(f"{self.end_term}")
        logger.info("TextMentionTermination condition created")
    
        # Create the team
        self.team = RoundRobinGroupChat([self.assistant], #, self.user_proxy],
                                        termination_condition=termination)
        logger.info("RoundRobin team created")

        logger.info(f">>>>> Completed Initializing Agentic System using model: {model.value} <<<<<\n")
        
    @classmethod
    async def async_init(cls, model: ModelName):
        """Async Factory method that initializes the Agentic system by connecting to the MCP server,
           creating the agents and start them"""

        logger.info(f">>>>> Start Initializing Agentic System using model: {model.value} <<<<<")

        mcp_tools_with_autogen = await AgentManager.connect_to_servers()

        logger.info(f"Connected to MCP servers with tools: {[tool.name for tool in mcp_tools_with_autogen]}")

        self = cls(model=model, mcp_tools=mcp_tools_with_autogen)
               
        return self

    async def shutdown(self):
        """Shutdown the AgentManager and its components."""
            
        await self.user_proxy.close()
        await self.assistant.close()
        logger.info("Agents are closed")
   
        await self.model_client.close()
        logger.info("Model client is closed")

    async def process_message(self, message: str) -> TaskResult:

        try:
            # Run the conversation and stream to the console.
            logger.debug("Running the team...")
            #stream = self.team.run_stream()#task="Welcome the user with nice 'Hello' and ask how you can assist")

            #result = await self.team.run_stream(task=message)
            a = TextMessage(content=message, source="user")
            request = TextMessage.model_validate(a)
            # await self.team.reset()  # Reset the team for a new task.
            stream = await self.team.run(task=request)

            # Remove 'self.end_term' from the response
            if stream.messages and self.end_term in stream.messages[-1].content:
                stream.messages[-1].content = stream.messages[-1].content.replace(self.end_term, "").strip()

            return stream
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Error processing message"
        
    async def process_message_stream(self, message: str):
        """
        Process messages through your AutoGen system with streaming
        """
        try:
            # Get the response from your AutoGen system
            #response = await self.process_message(message)
            #response_text = response.messages[-1].content if response.messages else "No response"

            # Try 0: Simulate streaming by yielding chunks of entire response, regardless of inner structure
            # words = response_text.split()
            # for i, word in enumerate(words):
            #     chunk_content = word + " " if i < len(words) - 1 else word
            #     yield chunk_content
            #     await asyncio.sleep(0.05)  # Small delay for streaming effect
             

            # Try 1: skipping markdown splitting
            # paragraphs = response_text.split('\n\n')
            
            # for para in paragraphs:
            #     if not para.strip():
            #         continue
                    
            #     # Send complete paragraphs for better Markdown rendering
            #     if (para.startswith('```') or para.startswith('#') or 
            #         para.startswith('- ') or para.startswith('* ') or
            #         para.startswith('> ')):
            #         # Send Markdown blocks as complete units
            #         yield para + '\n\n'
            #         await asyncio.sleep(0.3)
            #     else:
            #         # Regular text - can split by sentences
            #         sentences = para.split('. ')
            #         for i, sentence in enumerate(sentences):
            #             if i < len(sentences) - 1:
            #                 yield sentence + '. '
            #             else:
            #                 yield sentence + '\n\n'
            #             await asyncio.sleep(0.2)

            # Try 2: Using the Markdown streamer
            # Simulate your AutoGen system generating content
            async def autogen_generator():
                response = await self.process_message(message)
                response_text = response.messages[-1].content if response.messages else "No response"

                #full_response = await self.process_message(messages, model)
                
                # Break into chunks for streaming simulation
                chunks = self.markdown_streamer.detect_markdown_boundaries(response_text)
                
                for chunk in chunks:
                    # Simulate processing delay
                    await asyncio.sleep(0.2)
                    yield chunk + "\n\n"
            
            # Stream with markdown awareness
            async for chunk in self.markdown_streamer.stream_with_markdown_awareness(autogen_generator()):
                yield chunk
                    
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            yield f"Error: {str(e)}"

    async def user_input_func(self, prompt: str, cancellation_token: CancellationToken | None) -> str:
        logger.info(f"User input requested with prompt: {prompt}")
        return "continue"  # Simulate user input for now, replace with actual input logic

    def create_model_client(self, model: ModelName) -> ChatCompletionClient:
        """Create the agent(s) - for now, let's use a local reasoning models """

        model_client = None
        #load_dotenv() 
        #openai_model_client = OpenAIChatCompletionClient(model="gpt-4-turbo") #, api_key=OPENAI_API_KEY) # 
        #model_client=openai_model_client 

        if model == ModelName.GPT_OSS_20B:
            local_ollama_openai_model_client = OllamaChatCompletionClient(model="gpt-oss:20b", 
                                                                          model_info={"description": "Local Ollama GPT-OSS 20B model",
                                                                                      "vision": False,
                                                                                      "function_calling": True,
                                                                                  "json_output": True,
                                                                                  "family": ModelFamily.GPT_5,
                                                                                  "structured_output": True,
                                                                                  "reasoning_mode": "high"}
                                                                      ) 
            model_client=local_ollama_openai_model_client

        elif model == ModelName.QWEN3_30B_A3B:
            local_ollama_qwen_model_client = OllamaChatCompletionClient(model="qwen3:30b-a3b") # local
            model_client=local_ollama_qwen_model_client

        # local_ollama_qwen_model_client = OllamaChatCompletionClient(model="qwen3:30b", 
        #                                                             model_info={"description": "Local Ollama QWEN 30B model",
        #                                                                         "vision": False,
        #                                                                         "function_calling": True,
        #                                                                         "json_output": True,
        #                                                                         "family": ModelFamily.UNKNOWN,
        #                                                                         "structured_output": True
        #                                                                         }
        #                                                               )
        # model_client=local_ollama_qwen_model_client

        return model_client

    # Connect to all configured MCP servers
    # Input: none
    # Output: list of tools
    @staticmethod
    async def connect_to_servers() -> list[str]:
        """Connect to all configured MCP servers."""
        the_tools = []

        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)

            # NOTE: we can integrate other public (and trusted) MCP servers
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                logger.debug(f"Connecting to MCP server: '{server_name}' with config: {server_config}")

                # Can be done using async method
                mcp_server_with_autogen = StdioServerParams(**server_config, read_timeout_seconds=30)
                mcp_tools_with_autogen = await mcp_server_tools(mcp_server_with_autogen)
                logger.debug(f"Connected to MCP server '{server_name}', Available tools: {[tool.name for tool in mcp_tools_with_autogen]}")

                the_tools.extend(mcp_tools_with_autogen)

        except Exception as e:
            logger.error(f"Error loading server configuration: {e}")
            raise

        return the_tools

if __name__ == "__main__":
    agent_manager = asyncio.run(AgentManager.async_init())
