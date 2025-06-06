from datetime import datetime, timedelta
import os
import sys
import time
import shutil
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
from agent_networks.text_processing_agent import TextProcessingAgent
from agent_networks.eda_agent_network import EDAAgentNetwork
from agent_networks.text2sql_agent_network import Text2SQLAgentNetwork
from uuid import UUID
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from model import QueryRequest, DataFrameRequest, Text2SQLRequest, ConversationEntry, AgentResponse
import asyncio
from pathlib import Path
from runnable_config import SessionConfig
import json
import uuid
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, base_dir: str = "temp_storage", max_age_hours: int = 4):
        self.base_dir = Path(base_dir)
        self.max_age = timedelta(hours=max_age_hours)
        self._ensure_base_dir()
        
    def _ensure_base_dir(self):
        """Ensure the base directory exists."""
        self.base_dir.mkdir(exist_ok=True)
        
    def get_session_dir(self, session_id: UUID) -> Path:
        """Get the directory for a specific session."""
        session_dir = self.base_dir / str(session_id)
        session_dir.mkdir(exist_ok=True)
        return session_dir
        
    async def save_csv(self, session_id: UUID, file: UploadFile) -> str:
        """Save an uploaded CSV file to the session directory."""
        session_dir = self.get_session_dir(session_id)
        file_path = session_dir / file.filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        return str(file_path)
        
    def get_csv_data(self, session_id: UUID, filename: str) -> pd.DataFrame:
        """Read a CSV file from the session directory."""
        file_path = self.get_session_dir(session_id) / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return pd.read_csv(file_path)
        
    def cleanup_old_files(self):
        """Remove files older than max_age."""
        current_time = datetime.now()
        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue
                
            # Check if directory is older than max_age
            dir_time = datetime.fromtimestamp(session_dir.stat().st_mtime)
            if current_time - dir_time > self.max_age:
                shutil.rmtree(session_dir)
                
    def cleanup_all(self):
        """Remove all temporary files."""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
        self._ensure_base_dir()

class AgentNetworkManager:
    def __init__(self):
        self.networks: Dict[str, Optional[object]] = {
            'text': None,
            'eda': None,
            'text2sql': None
        }
        self.conversation_history: Dict[UUID, List[ConversationEntry]] = {}
        self.session_config = SessionConfig()  # Initialize session configuration

    def initialize_networks(self) -> None:
        """Initialize agent networks."""
        self.networks['text'] = TextProcessingAgent()
        self.networks['eda'] = EDAAgentNetwork()
        self.networks['text2sql'] = Text2SQLAgentNetwork()
        
        # Wait for networks to initialize
        print("Waiting for networks to initialize...")
        time.sleep(3)
        
        self._print_available_networks()

    def _print_available_networks(self) -> None:
        """Print information about available networks."""
        for network_type, network in self.networks.items():
            if network:
                print(f"\nAvailable {network_type.title()} Network:")
                print(f"- Status: Active")
                print(f"- Type: {network_type}")

    def add_conversation_entry(self, session_id: UUID, user_input: str, response: dict, agent_type: str) -> None:
        """Add a new entry to the conversation history and update session context."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        # Create or update session configuration
        self.session_config.create_session(session_id)
        
        # Add conversation entry
        self.conversation_history[session_id].append(
            ConversationEntry(
                timestamp=datetime.utcnow(),
                userInput=user_input,
                response=response,
                agentType=agent_type
            )
        )
        
        # Update session context
        self.session_config.update_context(session_id, {
            "agent_type": agent_type,
            "current_state": "completed",
            "metadata": {
                "last_query": user_input,
                "last_response": response
            }
        })

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

# Initialize storage manager
storage_manager = StorageManager()

# Initialize agent manager
agent_manager = AgentNetworkManager()

@app.on_event("startup")
async def startup_event():
    """Initialize networks when the FastAPI application starts."""
    # Clean up any existing temporary files and sessions
    storage_manager.cleanup_all()
    agent_manager.session_config.cleanup_old_sessions()
    # Initialize networks
    agent_manager.initialize_networks()
    # Start periodic cleanup task
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    """Periodically clean up old files and sessions."""
    while True:
        await asyncio.sleep(3600)  # Check every hour
        storage_manager.cleanup_old_files()
        agent_manager.session_config.cleanup_old_sessions()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up when the FastAPI application shuts down."""
    storage_manager.cleanup_all()

@text_processing_router.post("/ask", response_model=AgentResponse)
async def ask_query(request: QueryRequest):
    """Endpoint to process text queries through the text processing network."""
    if not agent_manager.networks['text']:
        raise HTTPException(status_code=500, detail="Text processing network not initialized")
    
    try:
        # Create or get session configuration
        agent_manager.session_config.create_session(request.sessionID)
        
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

@eda_router.post("/upload_csv")
async def upload_csv(session_id: UUID, file: UploadFile = File(...)):
    """Upload a CSV file for EDA analysis."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Create session configuration
        agent_manager.session_config.create_session(session_id)
        
        # Save file and update session config
        file_path = await storage_manager.save_csv(session_id, file)
        agent_manager.session_config.add_file_path(session_id, file_path, "csv")
        
        return JSONResponse(
            content={
                "message": "File uploaded successfully",
                "session_id": str(session_id),
                "filename": file.filename,
                "file_path": file_path
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@eda_router.post("/analyze_csv", response_model=AgentResponse)
async def analyze_csv_data(request: DataFrameRequest):
    """Analyze data from an uploaded CSV file."""
    if not agent_manager.networks['eda']:
        raise HTTPException(status_code=500, detail="EDA network not initialized")
    
    try:
        # Create or get session configuration
        agent_manager.session_config.create_session(request.sessionID)
        
        # Get DataFrame
        if request.dataframe:
            df = pd.DataFrame.from_dict(request.dataframe)
            agent_manager.session_config.add_dataframe(request.sessionID, "current_df", df)
        else:
            session_files = agent_manager.session_config.get_session_files(request.sessionID, "csv")
            if not session_files:
                raise HTTPException(status_code=400, detail="No CSV file found for this session")
            
            latest_file = session_files[-1]["path"]
            df = storage_manager.get_csv_data(request.sessionID, latest_file)
        
        # Process DataFrame
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
        # Create or get session configuration
        agent_manager.session_config.create_session(request.sessionID)
        
        # Update session context with schema
        agent_manager.session_config.update_context(request.sessionID, {
            "agent_type": "text2sql",
            "current_state": "processing",
            "metadata": {
                "schema": request.schema,
                "query": request.userInput
            }
        })
        
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
    """Get conversation history and session context for a specific session."""
    session_info = agent_manager.session_config.get_session(session_id)
    history = agent_manager.conversation_history.get(session_id, [])
    
    return {
        "session_id": session_id,
        "session_context": session_info,
        "history": history
    }

# Include the routers in the main app
app.include_router(text_processing_router)
app.include_router(eda_router)
app.include_router(text2sql_router)

def main():
    """Main function to run the FastAPI application."""
    uvicorn.run(app, host="0.0.0.0", port=8002)

if __name__ == "__main__":
    main()