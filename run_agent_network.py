import os
import subprocess
import sys
import time
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from text_processing_agent import TextProcessingAgent
from eda_agent_network import EDAAgentNetwork
from text2sql_agent_network import Text2SQLAgentNetwork
from uuid import UUID, uuid4
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Network API", description="API for interacting with the agent network")

# Create routers for different agent types
from fastapi import APIRouter
text_processing_router = APIRouter(prefix="/text_processing_agent", tags=["Text Processing"])
eda_router = APIRouter(prefix="/eda_agent", tags=["EDA"])
text2sql_router = APIRouter(prefix="/text2sql_agent", tags=["Text2SQL"])

class QueryRequest(BaseModel):
    userInput: str
    sessionID: UUID

class DataFrameRequest(BaseModel):
    userInput: str
    sessionID: UUID
    dataframe: Optional[Dict] = None  # JSON representation of DataFrame

class Text2SQLRequest(BaseModel):
    userInput: str
    sessionID: UUID
    schema: Optional[str] = None  # Database schema information

class ConversationEntry(BaseModel):
    timestamp: datetime
    userInput: str
    response: dict
    agentType: str

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
    if not os.getenv("DATA_ANALYSIS_PORT"):
        os.environ["DATA_ANALYSIS_PORT"] = "5003"
    if not os.getenv("DATA_VISUALIZATION_PORT"):
        os.environ["DATA_VISUALIZATION_PORT"] = "5004"
    if not os.getenv("DATA_WRANGLING_PORT"):
        os.environ["DATA_WRANGLING_PORT"] = "5005"
    if not os.getenv("NLQ_RECONSTRUCTION_PORT"):
        os.environ["NLQ_RECONSTRUCTION_PORT"] = "5007"
    if not os.getenv("GATING_PORT"):
        os.environ["GATING_PORT"] = "5008"
    if not os.getenv("DYNAMIC_FEW_SHOTS_PORT"):
        os.environ["DYNAMIC_FEW_SHOTS_PORT"] = "5009"
    if not os.getenv("SQL_GENERATION_PORT"):
        os.environ["SQL_GENERATION_PORT"] = "5010"
    
    # Start the text processing agents
    summarizer_process = start_agent("agents/summarizer.py", "Summarizer")
    translator_process = start_agent("agents/translator.py", "Translator")
    
    # Start the EDA agents
    analysis_process = start_agent("agents/data_analysis_agent.py", "Data Analysis")
    visualization_process = start_agent("agents/data_visualization_agent.py", "Data Visualization")
    wrangling_process = start_agent("agents/data_wrangling_agent.py", "Data Wrangling")
    
    # Start the Text2SQL agents
    nlq_process = start_agent("agents/nlq_reconstruction.py", "NLQ Reconstruction")
    gating_process = start_agent("agents/gating.py", "Gating")
    few_shots_process = start_agent("agents/dynamic_few_shots.py", "Dynamic Few Shots")
    sql_gen_process = start_agent("agents/sql_generation.py", "SQL Generation")
    
    # Wait for agents to start up
    print("Waiting for agents to start up...")
    time.sleep(3)
    
    return (summarizer_process, translator_process, analysis_process, visualization_process, wrangling_process,
            nlq_process, gating_process, few_shots_process, sql_gen_process)

# Global variables to store agent processes and networks
summarizer_process = None
translator_process = None
analysis_process = None
visualization_process = None
wrangling_process = None
nlq_process = None
gating_process = None
few_shots_process = None
sql_gen_process = None
text_network = None
eda_network = None
text2sql_network = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents when the FastAPI application starts."""
    global summarizer_process, translator_process, analysis_process, visualization_process, wrangling_process
    global nlq_process, gating_process, few_shots_process, sql_gen_process
    global text_network, eda_network, text2sql_network
    
    # Initialize all agents
    (summarizer_process, translator_process, analysis_process, visualization_process, wrangling_process,
     nlq_process, gating_process, few_shots_process, sql_gen_process) = initialize_agents()
    
    # Initialize networks
    text_network = TextProcessingAgent()
    eda_network = EDAAgentNetwork()
    text2sql_network = Text2SQLAgentNetwork()  # You'll need to create this class
    
    # List available agents
    print("\nAvailable Text Processing Agents:")
    for agent in text_network.list_agents():
        print(f"- {agent.get('name', 'Unnamed')}: {agent.get('description', 'No description')}")
    
    print("\nAvailable EDA Agents:")
    for agent in eda_network.list_agents():
        print(f"- {agent.get('name', 'Unnamed')}: {agent.get('description', 'No description')}")
    
    print("\nAvailable Text2SQL Agents:")
    for agent in text2sql_network.list_agents():
        print(f"- {agent.get('name', 'Unnamed')}: {agent.get('description', 'No description')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up processes when the FastAPI application shuts down."""
    for process in [summarizer_process, translator_process, analysis_process, visualization_process, wrangling_process,
                   nlq_process, gating_process, few_shots_process, sql_gen_process]:
        if process:
            process.terminate()
    print("All processes terminated.")

@text_processing_router.post("/ask")
async def ask_query(request: QueryRequest):
    """Endpoint to process text queries through the text processing network."""
    try:
        if not text_network:
            raise HTTPException(status_code=500, detail="Text processing network not initialized")
        
        # Process the query
        result = await text_network.process_text(request.userInput)
        
        # Store the conversation
        if request.sessionID not in conversation_history:
            conversation_history[request.sessionID] = []
        
        conversation_history[request.sessionID].append(
            ConversationEntry(
                timestamp=datetime.utcnow(),
                userInput=request.userInput,
                response=result,
                agentType="text_processing"
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

@eda_router.post("/ask")
async def analyze_data(request: DataFrameRequest):
    """Endpoint to process data analysis queries through the EDA network."""
    try:
        if not eda_network:
            raise HTTPException(status_code=500, detail="EDA network not initialized")
        
        if not request.dataframe:
            raise HTTPException(status_code=400, detail="No DataFrame provided")
        
        # Convert JSON to DataFrame
        df = pd.DataFrame.from_dict(request.dataframe)
        
        # Process the query
        result = await eda_network.process_dataframe(df, request.userInput)
        
        # Store the conversation
        if request.sessionID not in conversation_history:
            conversation_history[request.sessionID] = []
        
        conversation_history[request.sessionID].append(
            ConversationEntry(
                timestamp=datetime.utcnow(),
                userInput=request.userInput,
                response=result,
                agentType="eda"
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

@text2sql_router.post("/ask")
async def convert_to_sql(request: Text2SQLRequest):
    """Endpoint to process text-to-SQL conversion queries."""
    try:
        if not text2sql_network:
            raise HTTPException(status_code=500, detail="Text2SQL network not initialized")
        
        if not request.schema:
            raise HTTPException(status_code=400, detail="No database schema provided")
        
        # Process the query
        result = await text2sql_network.process_query(request.userInput, request.schema)
        
        # Store the conversation
        if request.sessionID not in conversation_history:
            conversation_history[request.sessionID] = []
        
        conversation_history[request.sessionID].append(
            ConversationEntry(
                timestamp=datetime.utcnow(),
                userInput=request.userInput,
                response=result,
                agentType="text2sql"
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

# Include the routers in the main app
app.include_router(text_processing_router)
app.include_router(eda_router)
app.include_router(text2sql_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 