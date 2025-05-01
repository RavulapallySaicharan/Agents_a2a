import os
import subprocess
import sys
import time
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from agent_network import TextProcessingNetwork

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Network API", description="API for interacting with the agent network")

class QueryRequest(BaseModel):
    query: str

def start_agent(agent_file, name):
    """Start an agent in a new process."""
    print(f"Starting {name} Agent...")
    try:
        process = subprocess.Popen([sys.executable, agent_file], 
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
        return process
    except Exception as e:
        print(f"Error starting {name} Agent: {str(e)}")
        return None

def initialize_agents():
    """Initialize the agent network."""
    # Check if either OpenAI API key or Azure OpenAI credentials are set
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_azure = (bool(os.getenv("AZURE_OPENAI_API_KEY")) and 
                bool(os.getenv("AZURE_OPENAI_ENDPOINT")) and 
                bool(os.getenv("AZURE_OPENAI_API_VERSION")))
    
    if not (has_openai or has_azure):
        raise HTTPException(status_code=500, detail="No valid API credentials found")
    
    if has_openai:
        print("Using OpenAI credentials")
    elif has_azure:
        print("Using Azure OpenAI credentials")
    
    # Set default ports if not specified
    if not os.getenv("SUMMARIZER_PORT"):
        os.environ["SUMMARIZER_PORT"] = "5001"
    if not os.getenv("TRANSLATOR_PORT"):
        os.environ["TRANSLATOR_PORT"] = "5002"
    
    # Start the agents
    summarizer_process = start_agent("agents/summarizer.py", "Summarizer")
    translator_process = start_agent("agents/translator.py", "Translator")
    
    # Wait for agents to start up
    print("Waiting for agents to start up...")
    time.sleep(3)
    
    return summarizer_process, translator_process

# Global variables to store agent processes and network
summarizer_process = None
translator_process = None
network = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents when the FastAPI application starts."""
    global summarizer_process, translator_process, network
    summarizer_process, translator_process = initialize_agents()
    network = TextProcessingNetwork()
    
    # List available agents
    print("\nAvailable Agents:")
    for agent in network.list_agents():
        print(f"- {agent.get('name', 'Unnamed')}: {agent.get('description', 'No description')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up processes when the FastAPI application shuts down."""
    if summarizer_process:
        summarizer_process.terminate()
    if translator_process:
        translator_process.terminate()
    print("All processes terminated.")

@app.post("/ask")
async def ask_query(request: QueryRequest):
    """Endpoint to process queries through the agent network."""
    try:
        if not network:
            raise HTTPException(status_code=500, detail="Agent network not initialized")
            
        result = await network.process_text(request.query)
        return {
            "agent": result["agent"],
            "confidence": result["confidence"],
            "response": result["result"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 