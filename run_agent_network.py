import os
import subprocess
import sys
import time
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from text_processing_agent import TextProcessingAgent
from uuid import UUID, uuid4
from typing import Dict, List
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Network API", description="API for interacting with the agent network")

# Create a router for text processing agent
from fastapi import APIRouter
text_processing_router = APIRouter(prefix="/text_processing_agent", tags=["Text Processing"])

class QueryRequest(BaseModel):
    userInput: str
    sessionID: UUID

class ConversationEntry(BaseModel):
    timestamp: datetime
    userInput: str
    response: dict
    agentType: str  # Added to identify which agent handled the request

# Store conversation history
conversation_history: Dict[UUID, List[ConversationEntry]] = {}

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
    network = TextProcessingAgent()
    
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

@text_processing_router.post("/ask")
async def ask_query(request: QueryRequest):
    """Endpoint to process queries through the agent network."""
    try:
        if not network:
            raise HTTPException(status_code=500, detail="Agent network not initialized")
        
        # Process the query
        result = await network.process_text(request.userInput)
        
        # Store the conversation
        if request.sessionID not in conversation_history:
            conversation_history[request.sessionID] = []
        
        conversation_history[request.sessionID].append(
            ConversationEntry(
                timestamp=datetime.utcnow(),
                userInput=request.userInput,
                response=result,
                agentType="text_processing"  # Identify this as a text processing agent interaction
            )
        )
        
        return {
            "session_id": request.sessionID,
            "agent": result["agent"],
            "confidence": result["confidence"],
            "response": result["response"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}")
async def get_conversation_history(session_id: UUID):
    """Get conversation history for a specific session across all agent types."""
    if session_id not in conversation_history:
        return {"session_id": session_id, "history": []}
    
    return {
        "session_id": session_id,
        "history": conversation_history[session_id]
    }

# Include the router in the main app
app.include_router(text_processing_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 