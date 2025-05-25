from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any
from uuid import UUID
import uvicorn
from session_manager import SessionManager
from pathlib import Path
import shutil
from python_a2a import Message, MessageRole, TextContent
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from contextlib import asynccontextmanager

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
        session_config = session_manager.get_session(session_id)
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
        # agent_response = f"Echo: {message}"
        if agent_flag == "eda_agent":
            # get the name of the dataframe based on the conversation history and the file_descriptions
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            conversation_history = session_config.get_conversation_history(session_id)
            file_descriptions = session_config.get_file_descriptions(session_id)
            # get the name of the dataframe based on the conversation history and the file_descriptions
            prompt = f"Based on the conversation history and the file descriptions, what is the name of the dataframe? conversation history: {conversation_history}, file descriptions: {file_descriptions}. Instruction: Just provide the name of the dataframe, don't provide any other text."
            response = llm.invoke(prompt)
            print("-------------------------------------")
            print("response:")
            print(response.content)
            print("-------------------------------------")


            df = session_config.get_dataframe(session_id, "df_" + response.content)
            agent = create_pandas_dataframe_agent(llm, df, agent_type="tool-calling", verbose=True, allow_dangerous_code=True)
            agent_response = agent.invoke({"input": message})
        else:
            agent_response = f"Echo: {message}"
        
        # Create agent message
        agent_message = Message(
            content=TextContent(text=agent_response),
            role=MessageRole.AGENT
        )
        
        # Add agent message to conversation history
        session_config.add_conversation_message(session_id, agent_message)
        
        # Get updated conversation history
        conversation_history = session_config.get_conversation_history(session_id)
        
        return {
            "status": "success",
            "session_id": str(session_id),
            "response": agent_response,
            "conversation_history": [
                {
                    "role": msg.role.value,
                    "content": msg.content.text,
                    "timestamp": msg.timestamp if hasattr(msg, 'timestamp') else None
                }
                for msg in conversation_history
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 