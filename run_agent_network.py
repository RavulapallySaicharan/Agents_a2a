from datetime import datetime
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import uvicorn
from text_processing_agent import TextProcessingAgent
from eda_agent_network import EDAAgentNetwork
from text2sql_agent_network import Text2SQLAgentNetwork
from uuid import UUID
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from model import QueryRequest, DataFrameRequest, Text2SQLRequest, ConversationEntry, AgentResponse

# Load environment variables
load_dotenv()

class AgentNetworkManager:
    def __init__(self):
        self.processes: Dict[str, Optional[subprocess.Popen]] = {}
        self.networks: Dict[str, Optional[object]] = {
            'text': None,
            'eda': None,
            'text2sql': None
        }
        self.conversation_history: Dict[UUID, List[ConversationEntry]] = {}
        self._validate_credentials()
        self._set_default_ports()

    def _validate_credentials(self) -> None:
        """Validate that either OpenAI or Azure OpenAI credentials are set."""
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_azure = (bool(os.getenv("AZURE_OPENAI_API_KEY")) and 
                    bool(os.getenv("AZURE_OPENAI_ENDPOINT")) and 
                    bool(os.getenv("AZURE_OPENAI_API_VERSION")))
        
        if not (has_openai or has_azure):
            raise HTTPException(status_code=500, detail="No valid API credentials found")
        
        print("Using OpenAI credentials" if has_openai else "Using Azure OpenAI credentials")

    def _set_default_ports(self) -> None:
        """Set default ports for all agents if not specified."""
        default_ports = {
            "SUMMARIZER_PORT": "5001",
            "TRANSLATOR_PORT": "5002",
            "DATA_ANALYSIS_PORT": "5003",
            "DATA_VISUALIZATION_PORT": "5004",
            "DATA_WRANGLING_PORT": "5005",
            "NLQ_RECONSTRUCTION_PORT": "5007",
            "GATING_PORT": "5008",
            "DYNAMIC_FEW_SHOTS_PORT": "5009",
            "SQL_GENERATION_PORT": "5010"
        }
        
        for port_name, default_port in default_ports.items():
            if not os.getenv(port_name):
                os.environ[port_name] = default_port

    def start_agent(self, agent_file: str, name: str) -> Optional[subprocess.Popen]:
        """Start an agent in a new process."""
        print(f"Starting {name} Agent...")
        try:
            process = subprocess.Popen(
                [sys.executable, agent_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes[name] = process
            return process
        except Exception as e:
            print(f"Error starting {name} Agent: {str(e)}")
            return None

    def initialize_agents(self) -> None:
        """Initialize all agents and their networks."""
        # Start text processing agents
        self.start_agent("agents/summarizer.py", "Summarizer")
        self.start_agent("agents/translator.py", "Translator")
        
        # Start EDA agents
        self.start_agent("agents/data_analysis_agent.py", "Data Analysis")
        self.start_agent("agents/data_visualization_agent.py", "Data Visualization")
        self.start_agent("agents/data_wrangling_agent.py", "Data Wrangling")
        
        # Start Text2SQL agents
        self.start_agent("agents/nlq_reconstruction.py", "NLQ Reconstruction")
        self.start_agent("agents/gating.py", "Gating")
        self.start_agent("agents/dynamic_few_shots.py", "Dynamic Few Shots")
        self.start_agent("agents/sql_generation.py", "SQL Generation")
        
        # Initialize networks
        self.networks['text'] = TextProcessingAgent()
        self.networks['eda'] = EDAAgentNetwork()
        self.networks['text2sql'] = Text2SQLAgentNetwork()
        
        # Wait for agents to start up
        print("Waiting for agents to start up...")
        time.sleep(3)
        
        self._print_available_agents()

    def _print_available_agents(self) -> None:
        """Print information about available agents in each network."""
        for network_type, network in self.networks.items():
            if network:
                print(f"\nAvailable {network_type.title()} Agents:")
                for agent in network.list_agents():
                    print(f"- {agent.get('name', 'Unnamed')}: {agent.get('description', 'No description')}")

    def cleanup(self) -> None:
        """Terminate all agent processes."""
        for process in self.processes.values():
            if process:
                process.terminate()
        print("All processes terminated.")

    def add_conversation_entry(self, session_id: UUID, user_input: str, response: dict, agent_type: str) -> None:
        """Add a new entry to the conversation history."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append(
            ConversationEntry(
                timestamp=datetime.utcnow(),
                userInput=user_input,
                response=response,
                agentType=agent_type
            )
        )

# Initialize FastAPI app
app = FastAPI(title="Agent Network API", description="API for interacting with the agent network")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create routers
from fastapi import APIRouter
text_processing_router = APIRouter(prefix="/text_processing_agent", tags=["Text Processing"])
eda_router = APIRouter(prefix="/eda_agent", tags=["EDA"])
text2sql_router = APIRouter(prefix="/text2sql_agent", tags=["Text2SQL"])

# Initialize agent manager
agent_manager = AgentNetworkManager()

@app.on_event("startup")
async def startup_event():
    """Initialize agents when the FastAPI application starts."""
    agent_manager.initialize_agents()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up processes when the FastAPI application shuts down."""
    agent_manager.cleanup()

@text_processing_router.post("/ask", response_model=AgentResponse)
async def ask_query(request: QueryRequest):
    """Endpoint to process text queries through the text processing network."""
    if not agent_manager.networks['text']:
        raise HTTPException(status_code=500, detail="Text processing network not initialized")
    
    try:
        result = await agent_manager.networks['text'].process_text(request.userInput)
        agent_manager.add_conversation_entry(request.sessionID, request.userInput, result, "text_processing")
        return AgentResponse(
            session_id=request.sessionID,
            agent=result["agent"],
            confidence=result["confidence"],
            response=result["response"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eda_router.post("/ask", response_model=AgentResponse)
async def analyze_data(request: DataFrameRequest):
    """Endpoint to process data analysis queries through the EDA network."""
    if not agent_manager.networks['eda']:
        raise HTTPException(status_code=500, detail="EDA network not initialized")
    
    if not request.dataframe:
        raise HTTPException(status_code=400, detail="No DataFrame provided")
    
    try:
        df = pd.DataFrame.from_dict(request.dataframe)
        result = await agent_manager.networks['eda'].process_dataframe(df, request.userInput)
        agent_manager.add_conversation_entry(request.sessionID, request.userInput, result, "eda")
        return AgentResponse(
            session_id=request.sessionID,
            agent=result["agent"],
            confidence=result["confidence"],
            response=result["response"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@text2sql_router.post("/ask", response_model=AgentResponse)
async def convert_to_sql(request: Text2SQLRequest):
    """Endpoint to process text-to-SQL conversion queries."""
    if not agent_manager.networks['text2sql']:
        raise HTTPException(status_code=500, detail="Text2SQL network not initialized")
    
    if not request.schema:
        raise HTTPException(status_code=400, detail="No database schema provided")
    
    try:
        result = await agent_manager.networks['text2sql'].process_query(request.userInput, request.schema)
        agent_manager.add_conversation_entry(request.sessionID, request.userInput, result, "text2sql")
        return AgentResponse(
            session_id=request.sessionID,
            agent=result["agent"],
            confidence=result["confidence"],
            response=result["response"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}")
async def get_conversation_history(session_id: UUID):
    """Get conversation history for a specific session across all agent types."""
    if session_id not in agent_manager.conversation_history:
        return {"session_id": session_id, "history": []}
    
    return {
        "session_id": session_id,
        "history": agent_manager.conversation_history[session_id]
    }

# Include the routers in the main app
app.include_router(text_processing_router)
app.include_router(eda_router)
app.include_router(text2sql_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)