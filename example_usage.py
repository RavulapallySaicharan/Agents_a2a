from uuid import uuid4
from runnable_config import SessionConfig
from python_a2a import Message, Conversation, MessageRole, TextContent, A2AClient
import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from uuid import UUID
import uvicorn
import shutil
import json

# Initialize FastAPI app
app = FastAPI(title="Session Management API")

# Initialize SessionConfig for a default session
sessions = {"default": SessionConfig()}

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
        if session_id not in sessions:
            sessions[session_id] = SessionConfig()
        
        session_config = sessions[session_id]
        session_config.create_session(session_id)
        
        # Create temporary file
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / file.filename
        
        try:
            # Save uploaded file temporarily
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            print("file uploaded successfully.........")
            
            # Process the file
            result = session_config.process_file(session_id, str(temp_path))

            print("file processed successfully.........")
            
            # Add file to session configuration
            session_config.add_file_path(session_id, str(temp_path), file.filename.split(".")[-1])

            print("file added to session configuration successfully.........")
            
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

@app.get("/get_config_info")
def get_config_info(session_id: UUID) -> Dict[str, Any]:
    """Get the configuration information for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id].get_session(session_id)

def main():
    """Run the FastAPI application."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main() 