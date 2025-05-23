from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from uuid import UUID
import uvicorn
from runnable_config import SessionConfig
import os
from pathlib import Path
import shutil
import json

app = FastAPI(title="Session Management API")

# Initialize SessionConfig
session_config = SessionConfig()

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
    """Upload and process a file."""
    try:
        # Create session if it doesn't exist
        session_config.create_session(session_id)
        
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
            
            # Add file to session configuration
            session_config.add_file_path(session_id, str(temp_path), file.filename.split(".")[-1])
            
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
    """Get session information including files and dataframes."""
    try:
        session = session_config.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return {
            "session_id": str(session_id),
            "created_at": session["created_at"],
            "last_updated": session["last_updated"],
            "files": session["files"],
            "dataframes": session["dataframes"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/dataframe/{name}")
async def get_dataframe(session_id: UUID, name: str) -> Dict[str, Any]:
    """Get a specific DataFrame from the session."""
    try:
        df = session_config.get_dataframe(session_id, name)
        if df is None:
            raise HTTPException(status_code=404, detail="DataFrame not found")
            
        description = session_config.get_dataframe_description(session_id, name)
        
        return {
            "name": name,
            "data": df.to_dict(orient="records"),
            "columns": df.columns.tolist(),
            "description": description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/conversation")
async def get_conversation(session_id: UUID) -> Dict[str, Any]:
    """Get the conversation history for a session."""
    try:
        history = session_config.get_conversation_history(session_id)
        return {
            "session_id": str(session_id),
            "messages": [{"role": msg.role.value, "content": msg.content.text} for msg in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/{session_id}/message")
async def add_message(
    session_id: UUID,
    message: Dict[str, Any]
) -> Dict[str, Any]:
    """Add a message to the session conversation."""
    try:
        from python_a2a import Message, TextContent, MessageRole
        
        # Create Message object
        msg = Message(
            content=TextContent(text=message["content"]),
            role=MessageRole.USER if message["role"] == "user" else MessageRole.AGENT
        )
        
        # Add message to session
        session_config.add_conversation_message(session_id, msg)
        
        return {
            "status": "success",
            "message": "Message added successfully",
            "session_id": str(session_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: UUID) -> Dict[str, Any]:
    """Delete a session and all its data."""
    try:
        session_dir = session_config.get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
        return {
            "status": "success",
            "message": "Session deleted successfully",
            "session_id": str(session_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 