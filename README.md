# 🎓 ai-eng-course-project 
AI Engineering course of The hebrew University of Jerusalem - final project


# 🚀 Quick Start
Assuming you completed all the steps below, have all required packacges etc, to strat the project:
1. Run Docker Desktop, start 'open-webui' container (if not already running) 
2. Run Ollama (if not already running)
3. Start the nutrition_service.py from command line
4. Navigate to http://localhost:8080/ (Open WebUI), select the model wrapper to work with and start chatting


# 🛠️ Prerequisites
All of the below refer to MACOS and not Windows Operating System.\
Yet, most of it should work for Windows out of the box, some may need small adjustments.

- Python: 3.13.5 ( + recommend to have a virtual environment)
- Install all packages based on requirements.txt by running\
  `> pip install -r requirements.txt`
- Install and run __Docker__ Desktop (to run Open WebUI easily)
- Install and run __Ollama__ (to run and use local free models)
- Install qwen3:30b-a3b and gpt-oss:20b models (15 to 18 GB each, good for reasoning and Agentic work..)\
  Example: 
  `> ollama pull qwen3:30b`\
  __Note__: You can use just one model. Make sure to select the right one from Open WebUI before starting to chat


# 🧑‍💻 Local agents service
This local service allows Open WebUI / Ollama UI to communicate with the agentic project as it was a model by wrapping it with a web service exposing OpenAI APIs schema.

## Start the local service
`> python3 nutrition_service.py`

You may start it also from Visual Studio Code (e.g. for debugging)

## Shutdown the local service
`> CTRL+C`

If you kill the service or just close the terminal, the port may remain in use 

## Check the API
1. Open browser
2. Navigate to http://localhost:8000/docs
3. You will see the interactive Swagger UI.\
Find the POST /v1/chat/completions endpoint, click "Try it out".\
Fill in the request body, and click "Execute" to simulate an API call.

Alternatively, you can use browser extensions like "REST Client" or "Postman", or use JavaScript in the browser console to send a request.


# 🖥️ Open WebUI setup
Open WebUI allows connecting to any server that implements the OpenAI-compatible API - like ours.\
see https://docs.openwebui.com/getting-started/quick-start/starting-with-openai-compatible

## Download Open WebUI (with Docker)
Pull Open WebUI docker image\
`> docker pull ghcr.io/open-webui/open-webui:main`

## Run Open WebUI container (with Docker)
1. Create a folder for Open WebUI
2. Create a sub-folder named 'open-webui' - this subfolder will keep all your settings and chat history
3. From console, navigate to the folder just created and run\
`>docker run -d  -v open-webui:/app/backend/data -e WEBUI_AUTH=False --net=host --name open-webui --restart always ghcr.io/open-webui/open-webui:main` 

* First launch may take a minute or so - the Open WebUI is fetching some required packages during startup 
* Go to your browser and naviage to 
http://localhost:8080/
* Check your Docker Desktop - you should see the container just created up and running
* Next time you can just run the container form Docker Desktop UI by clicking the Play button next to the container

## Config Open WebUI to be familiar with our Wrapper Service 
1. Navigate to http://localhost:8080/ 
2. Go to 'User' (left bottom corner)
3. [Old version] Click 'Settings' -> Click 'Admin Settings' -> Select 'Connection'
4. [New Version] Click 'Admin Panel' -> Click 'Settings' -> Select 'Connection'
6. Click the '+' on the right line of 'OpenAI API'
7. Add 'http://host.docker.internal:8000/v1'
8. Test the connection by clicking the small refersh button on the right.
Connection should succeed
9. Save 
10. Click the 'New Chat' on the top left corner
10. Select our model, if not already selected ('Agentic-System-...')
11. Start chatting for a delicius meal 😋 🍲


# 🗄️ MCP Server
Our MCP Server is running locally as well i.e. using STDIO transport
It exposes the different tools (like meal-options) and used by the agentic system

## Check the mcp server using inspector tool (Optional)
1. Run the following command from command line (make sure you are in the correct path)
`>npx @modelcontextprotocol/inspector python3 mcp_food_server.py`
2. The browser should open automatically, navigating to a localhost mcp inspector service
3. Make sure the 'Transport Type' is _STDIO_ and Command is _python3_ and click 'Connect' to connect the server 
4. If all is good, you can click the 'Tools' icon on the top barto see the tools exposed by our mcp server
5. Make sure to properly shut down the server when done with `CTRL+C` from command line

# ⏭️ What's Next
?