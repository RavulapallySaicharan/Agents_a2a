from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from python_a2a import AgentNetwork, AIAgentRouter, Message, Conversation, MessageRole, TextContent, A2AClient
import json
import time

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Communication API")

class AgentRequest(BaseModel):
    agent_flag: str
    inputs: Dict[str, Any]

def load_agent_config():
    with open('agents/config.json', 'r') as f:
        return json.load(f)

def get_agent_url(port):
    return f"http://localhost:{port}"

@app.post("/ask_agent")
async def ask_agent(request: AgentRequest):
    try:
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
        
        # Create a conversation
        conversation = Conversation()
        conversation.add_message(user_message)
        
        # Time the response
        start_time = time.time()
        
        # Get the response by sending the message
        bot_response = client.send_message(user_message)
        conversation.add_message(bot_response)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Extract the latest response
        latest_response = conversation.messages[-1]
        
        return {
            "response": latest_response.content.text,
            "elapsed_time": elapsed_time,
            "conversation_summary": {
                "total_messages": len(conversation.messages),
                "user_messages": sum(1 for m in conversation.messages if m.role == MessageRole.USER),
                "assistant_messages": sum(1 for m in conversation.messages if m.role == MessageRole.AGENT)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 