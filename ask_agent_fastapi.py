from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from python_a2a import AgentNetwork, AIAgentRouter, Message, Conversation, MessageRole, TextContent, A2AClient
from runnable_config import SessionConfig
from uuid import UUID
import json
import time
import shutil

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Communication API")

# Initialize session management
sessions = {"default": SessionConfig()}

class AgentRequest(BaseModel):
    agent_flag: str
    inputs: Dict[str, Any]

def load_agent_config():
    with open('agents/config.json', 'r') as f:
        return json.load(f)

def get_agent_url(port):
    return f"http://localhost:{port}"

async def get_session_id(x_session_id: str = Header(..., description="Session ID in UUID format")) -> UUID:
    """Validate and return session ID from header."""
    try:
        return UUID(x_session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

@app.post("/ask_agent")
async def ask_agent(
    request: AgentRequest,
    session_id: UUID = Depends(get_session_id)
):
    try:
        # Initialize or get session
        if session_id not in sessions:
            sessions[session_id] = SessionConfig()
        session_config = sessions[session_id]
        
        # Load agent configuration
        config = load_agent_config()
        
        # Find the selected agent by flag
        selected_agent = None
        for agent in config['agents']:
            if agent['flag'] == request.agent_flag:
                selected_agent = agent
                break
        
        if not selected_agent:
            raise HTTPException(status_code=404, detail=f"Agent with flag '{request.agent_flag}' not found")
        
        # Create client for selected agent
        agent_url = get_agent_url(selected_agent['port'])
        client = A2AClient(agent_url)
        
        # Format the inputs into a message
        formatted_inputs = json.dumps(request.inputs, indent=2)
        
        # Create a message with the formatted inputs
        user_message = Message(
            content=TextContent(text=formatted_inputs),
            role=MessageRole.USER
        )
        
        # Add user message to session
        session_config.add_conversation_message(session_id, user_message)
        
        # Time the response
        start_time = time.time()
        
        # Get the response by sending the message
        bot_response = client.send_message(user_message)
        
        # Add bot response to session
        session_config.add_conversation_message(session_id, bot_response)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Get conversation history from session
        conversation_history = session_config.get_conversation_history(session_id)
        
        return {
            "response": bot_response.content.text,
            "elapsed_time": elapsed_time,
            "session_id": str(session_id),
            "conversation_summary": {
                "total_messages": len(conversation_history),
                "user_messages": sum(1 for m in conversation_history if m.role == MessageRole.USER),
                "assistant_messages": sum(1 for m in conversation_history if m.role == MessageRole.AGENT)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/conversation")
async def get_conversation(session_id: UUID):
    """Get the conversation history for a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session_config = sessions[session_id]
        history = session_config.get_conversation_history(session_id)
        
        return {
            "session_id": str(session_id),
            "messages": [{"role": msg.role.value, "content": msg.content.text} for msg in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: UUID):
    """Delete a session and all its data."""
    try:
        if session_id in sessions:
            session_config = sessions[session_id]
            session_dir = session_config.get_session_dir(session_id)
            if session_dir.exists():
                shutil.rmtree(session_dir)
            del sessions[session_id]
            
        return {
            "status": "success",
            "message": "Session deleted successfully",
            "session_id": str(session_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 