# Another magic function to write the code to a file

import asyncio
import json
import logging
#from dotenv import load_dotenv
#from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient 
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent 
from autogen_agentchat.conditions import TextMentionTermination 
from autogen_agentchat.teams import RoundRobinGroupChat 
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.ui import Console 
from custom_logger import logger

#assistant = None
#user_proxy = None

class AgentManager:
    def __init__(self):
        pass

    @classmethod
    async def async_init(cls):
        """Initialize the Agentic system by connecting to the MCP server, creating the agents and start them"""

        self = cls()
        
        model_client = create_model_client()
        logger.info(f"Using model client: {model_client.__class__.__name__}")

        mcp_tools_with_autogen = await connect_to_servers()

        logger.info(f"Connected to MCP servers with tools: {[tool.name for tool in mcp_tools_with_autogen]}")
        logger.info("Starting Food chatbot based on AutoGen Agents!")

        # self.assistant = AssistantAgent(
        #     name="assistant",
        #     llm_config={"model": model}
        # )
        # self.user = UserProxyAgent(name="user", human_input_mode="NEVER")


        # try:

        #     print("\n*** Creating AssistantAgent to work with all the tools -> Should have agent per MCP server - TODO...")
        #     assistant = AssistantAgent( name="assistant",
        #                     model_client=model_client,
        #                     tools=mcp_tools_with_autogen,
        #                     reflect_on_tool_use=True,  # Enable reflection on tool use
        #                     system_message="""Your name is Assistant.
        #                     You are a helpful assistant that answers general questions directly.
        #                     You are also able to use the supplied tools but only if you don't know the answer, you can use the tools.
        #                     Inform the user about the tools you have accessed and how to use them.
        #                     If you use a tool, reply with the tool's result only.
        #                     /no_think"""
        #     )

        #     print("*** Creating UserProxyAgent")
        #     user_proxy = UserProxyAgent(name="user_proxy",
        #                                 input_func=input)  # Use input() to get user input from console.

        #     # Create the termination condition which will end the conversation when the user says "APPROVE".
        #     print("*** Creating TextMentionTermination condition")
        #     termination = TextMentionTermination("quit")

        #     # Create the team.
        #     print("*** Creating a RoundRobin team")
        #     team = RoundRobinGroupChat([assistant, user_proxy], termination_condition=termination)

        #     # Run the conversation and stream to the console.
        #     print("*** Running the team...")
        #     stream = team.run_stream()#task="Welcome the user with nice 'Hello' and ask how you can assist")

        #     print("*** Starting Console Stream")
        #     print("\nType your queries or 'quit' to exit...")
        #     await Console(stream)

        # finally:
        #     print("\n*** Closing the agents")        
        #     await user_proxy.close()
        #     await assistant.close()

        #     print("\n*** Closing the model client\n\n")
        #     await my_model_client.close()
        return self

    # TODO EREZ - Required ??
    # async def shutdown(self):
    #     """Shutdown the AgentManager and its components."""
    #     await self.user.close()
    #     await self.assistant.close()

    #     print("\n*** Closing the agents")        
    #     await user_proxy.close()
    #     await assistant.close()

    #     print("\n*** Closing the model client\n\n")
    #     await my_model_client.close()
    #     print("\n*** Closed all agents and model client")

    def process_message(self, message: str) -> str:
        self.user.initiate_chat(self.assistant, message=message)
        return self.assistant.last_message()["content"]


def create_model_client() -> ChatCompletionClient:
    """Create the agent(s) - for now, let's use a local reasoning models """

    #load_dotenv() 
    #openai_model_client = OpenAIChatCompletionClient(model="gpt-4-turbo") #, api_key=OPENAI_API_KEY) # 
    #local_ollama_openai_model_client = OllamaChatCompletionClient(model="gpt-oss:20b") # local - add model_info ?
    local_ollama_qwen_model_client = OllamaChatCompletionClient(model="qwen3:30b-a3b") # local

    #model_client=openai_model_client 
    #model_client=local_ollama_openai_model_client
    model_client=local_ollama_qwen_model_client

    return model_client

# Connect to all configured MCP servers
# Input: none
# Output: list of tools
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
            mcp_server_with_autogen = StdioServerParams(**server_config)
            mcp_tools_with_autogen = await mcp_server_tools(mcp_server_with_autogen)
            logger.debug(f"Connected to MCP server '{server_name}', Available tools: {[tool.name for tool in mcp_tools_with_autogen]}")

            the_tools.extend(mcp_tools_with_autogen)

    except Exception as e:
        logger.error(f"Error loading server configuration: {e}")
        raise

    return the_tools

#if __name__ == "__main__":
#     asyncio.run(AgentManager.async_init())
if __name__ == "__main__":
    agent_manager = asyncio.run(AgentManager.async_init())
