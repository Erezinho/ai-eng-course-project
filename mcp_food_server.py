import json
import random
import os
from typing import List
from mcp.server.fastmcp import FastMCP
from custom_logger import logger
from search_engine import HybridSearch

DB_DIRECTORY = "local_db"

logger.info(f"Starting MCP Food Server. Using DB_DIRECTORY: {DB_DIRECTORY}")

# Initialize FastMCP server
mcp = FastMCP("food-server")

# Initialize HybridSearch
hybrid_search = HybridSearch()

@mcp.tool()
def help() -> str:
    """
    Helper function with available tools.

    Returns:
        A string containing the help message.
    """
    return (
        "Available tools:\n"
        "1. help() - Get a list of available tools.\n"
        "2. get_meal_options(calorie_limit: int, protein_goal: int, num_options: int = 3) - Get meal options based on nutritional constraints.\n"
    )

@mcp.tool()
def get_meal_options(query: str, intermediate_results: int = 4, final_results: int = 2) -> List[str]:
    """
    Uses the search engine class to get most relevant meals base on the query.
    The search is performed using both BM25 and vector similarity with cross-encoding for reranking.

    Args:
        query (str): The prompt text for the meal search.
        intermediate_results (int): The number of intermediate results to consider by hybrid search.
        final_results (int): The number of final results to return after cross-encoding.

    Returns:
        A list of strings. Each string represents a meal option with all nutritional information.
    """
    return hybrid_search.invoke(query, intermediate_results, final_results)

#@mcp.tool()
def get_meal_options_naive(calorie_limit: int, protein_goal: int, num_options: int = 3) -> List[dict]:
    """
    Naively filters recipes from ta json database based on nutritional constraints (as a POC).
    
    """
    json_file_path = os.path.join(DB_DIRECTORY, "recipes.json")
    with open(json_file_path, "r") as f:
        data = json.load(f)

    if not data:
        logger.error(f"Error reading json database file from: {json_file_path}")
        return ["Error reading json database file."]

    candidates = [
        recipe for recipe in data 
            if recipe['nutrition']['calories'] <= calorie_limit and recipe['nutrition']['protein'] >= protein_goal
    ]

    if len(candidates) > num_options:
        return random.sample(candidates, num_options)
    
    if len(candidates) == 0:
        return ["No suitable recipes found."]
        
    return candidates

@mcp.tool()
def get_image_for_meal(meal_name: str) -> bytes:
    """
    Retrieves the image bytes for a specific meal.

    Args:
        meal_name (str): The name of the meal.

    Returns:
        bytes: The image bytes.
    """
    image_path = os.path.join(DB_DIRECTORY, "qwen-image_todo_meal.png")
    with open(image_path, "rb") as f:
        return f.read()


# TODO EREZ - Add Honeypots toolset to let the MCP client know how to handle inappropriate requests
# Examples from the article in GeekTime:
# func1: HoneyPot_Flag_UnconventionalSyntax ;
# description1: "Identifies prompts with unconventional syntax or overly complex formatting such as Markdown, encoding, or placeholder tokens
# func2: HoneyPot_Probe_SystemPrompts
# description2: "Detects attempts to extract system-level instructions, internal prompts, or configuration details."

# When running the file directly, this code will be executed, starting the MCP server.
# If this file is imported as a module, the server will not start automatically 
# (i.e. this code will not be executed).
if __name__ == "__main__":
    # Initialize and run the server using local transport
    mcp.run(transport='stdio')
