from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.responses import JSONResponse
from python_a2a import AgentNetwork, AIAgentRouter, Message, Conversation, MessageRole, TextContent, A2AClient
from typing import Dict, Any
from uuid import UUID
import uvicorn
import json
from session_manager import SessionManager
from pathlib import Path
import shutil
from python_a2a import Message, MessageRole, TextContent
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from contextlib import asynccontextmanager
from pydantic import BaseModel
# Initialize SessionManager
session_manager = SessionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize any resources if needed
    yield
    # Shutdown: Clean up resources
    session_manager.cleanup_all()
    if Path("temp_storage").exists():
        # remove folders in the temp_storage folder
        for item in Path("temp_storage").iterdir():
            if item.is_dir():
                shutil.rmtree(item)

app = FastAPI(
    title="Multi-Session Management API",
    description="API for managing multiple sessions with file upload and information retrieval",
    lifespan=lifespan
)

async def get_session_id(x_session_id: str = Header(..., description="Session ID in UUID format")) -> UUID:
    """Validate and return session ID from header."""
    try:
        return UUID(x_session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")


class AgentRequest(BaseModel):
    agent_flag: str
    inputs: Dict[str, Any]

def load_agent_config():
    with open('agents/config.json', 'r') as f:
        return json.load(f)


def get_agent_url(port):
    return f"http://localhost:{port}"


def create_agent_inputs(message, session_id, conversation_history, file_name):
    """Collect all required inputs for the selected agent based on its configuration."""
    inputs = {}
    inputs["text"] = message
    inputs["session_id"] = str(session_id)
    conversation = []
    for each in conversation_history:
        if each.role == MessageRole.USER:
            conversation.append({"role": "user", "content": each.content.text})
        elif each.role == MessageRole.AGENT:
            conversation.append({"role": "agent", "content": each.content.text})
    inputs["conversation_history"] = conversation
    inputs["file_name"] = file_name
    return json.dumps(inputs, indent=2)


def display_available_agents(config):
    """Display all available agents."""
    output = []
    for idx, agent in enumerate(config['agents'], 1):
        output.append(agent['agent_flag'])
    return output


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: UUID = Depends(get_session_id)
) -> Dict[str, Any]:
    """Upload and process a file.
    
    Args:
        file: The file to upload
        session_id: Session ID from header
        
    Returns:
        Dict containing upload status and file information
    """
    try:
        # Get or create session
        session_config = session_manager.create_session(session_id)
        
        # Create temporary file
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / file.filename
        
        try:
            # Save uploaded file temporarily
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Process the file
            result = session_config.process_file(session_id, str(temp_path))
            
            return {
                "status": "success",
                "message": "File processed successfully",
                "session_id": str(session_id),
                "file_info": result
            }
            
        finally:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session_info(session_id: UUID) -> Dict[str, Any]:
    """Get complete session information.
    
    Args:
        session_id: The session ID
        
    Returns:
        Dict containing all session information including:
        - Basic session info (created_at, last_updated)
        - Files
        - DataFrames with descriptions
        - Conversation history
    """
    try:
        session_config = session_manager.get_session(session_id)
        if not session_config:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = session_config.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session data not found")
            
        # Get DataFrame descriptions
        dataframes = {}
        for df_name in session.get("dataframes", {}):
            df = session_config.get_dataframe(session_id, df_name)
            description = session_config.get_dataframe_description(session_id, df_name)
            if df is not None:
                dataframes[df_name] = {
                    "columns": df.columns.tolist(),
                    "shape": df.shape,
                    "description": description
                }
        
        # Get conversation history
        conversation = session.get("conversation", {})
        
        return {
            "session_id": str(session_id),
            "created_at": session["created_at"],
            "last_updated": session["last_updated"],
            "files": session["files"],
            "dataframes": dataframes,
            "conversation": conversation,
            "file_descriptions": session["file_descriptions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions() -> Dict[str, Dict]:
    """Get information about all active sessions."""
    try:
        return session_manager.get_all_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def delete_session(session_id: UUID) -> Dict[str, Any]:
    """Delete a session and its associated data."""
    try:
        session_config = session_manager.get_session(session_id)
        if not session_config:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # Clean up session data
        session_config.cleanup_all()
        
        # Remove session from manager
        session_manager.cleanup_all()
        
        return {
            "status": "success",
            "message": f"Session {session_id} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/discoverable_agents")
async def discoverable_agents() -> list[str]:
    """Get all discoverable agents."""
        # Load agent configuration
    config = load_agent_config()
    
    # Display available agents
    return display_available_agents(config)

@app.post("/ask_agent")
async def ask_agent(
    message: str,
    session_id: UUID = Depends(get_session_id),
    agent_flag: str = Query(..., description="The agent to use")
) -> Dict[str, Any]:
    """Send a message to the agent and get a response.
    
    Args:
        message: The message to send to the agent
        session_id: Session ID from header
        
    Returns:
        Dict containing the agent's response and updated conversation history
    """
    try:
        session_config = session_manager.create_session(session_id)
        if not session_config:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # Create user message
        user_message = Message(
            content=TextContent(text=message),
            role=MessageRole.USER
        )
        
        # Add user message to conversation history
        session_config.add_conversation_message(session_id, user_message)
        
        # TODO: Add actual agent processing logic here
        # For now, we'll just echo back a simple response

        # get the name of the dataframe based on the conversation history and the file_descriptions
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        conversation_history = session_config.get_conversation_history(session_id)
        file_descriptions = session_config.get_file_descriptions(session_id)
        # get the name of the dataframe based on the conversation history and the file_descriptions
        prompt = f"""You are an intelligent assistant that decides whether a file is needed to answer a user's question based on the conversation history and uploaded file descriptions.

                Inputs:
                - conversation history: {conversation_history}
                - file descriptions: {file_descriptions}

                Instruction:
                1. First, determine if the user's question can be answered **without referring to any files**. If the user's input provides all necessary information (e.g., simple summarization, counting words, or evaluating a known phrase), then return `None`.
                2. If a file is needed, select the **most recently uploaded file** that is **relevant** to the user's question based on the file descriptions and context.
                3. Only return the **name of the relevant file or `None`**. Do not include any other text or explanation.
                4. Be strict — only select a file if it is clearly required to perform the task.

                Return:
                - Just the name of the file (e.g., `document1`) or `None`.
                """
        response = llm.invoke(prompt)
        file_name = response.content.split(".")[0]

        print("file name :", file_name)

        # Load agent configuration
        config = load_agent_config()

        discoverable_agents = display_available_agents(config)

        # check if the agent_flag is in the config
        if agent_flag in discoverable_agents:
            selected_agent = config['agents'][discoverable_agents.index(agent_flag)]
            agent_url = get_agent_url(selected_agent['port'])
            client = A2AClient(agent_url)
        else:
            raise HTTPException(status_code=400, detail="Invalid agent flag")
        
        # Collect all required inputs for the agent
        agent_inputs = create_agent_inputs(message, session_id, conversation_history, file_name)

        # Create a message with the formatted inputs
        user_message = Message(
            content=TextContent(text=agent_inputs),
            role=MessageRole.USER
        )

        # get the response from the agent
        agent_response = client.send_message(user_message)
        
        # Create agent message
        agent_message = Message(
            content=TextContent(text=agent_response.content.text),
            role=MessageRole.AGENT
        )
        
        # Add agent message to conversation history
        session_config.add_conversation_message(session_id, agent_message)
        
        # Get updated conversation history
        conversation_history = session_config.get_conversation_history(session_id)
        
        return {
            "dataType": "data",
            "message": agent_response.content.text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 