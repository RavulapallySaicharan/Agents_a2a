from fastapi import FastAPI, Request, HTTPException
import httpx
import json
import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Router Gateway")

# Load agent configurations
CONFIG_PATH = "agents/config.json"

def load_agent_configs() -> Dict[str, Dict[str, Any]]:
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            return {agent["name"]: agent for agent in config["agents"]}
    except Exception as e:
        logger.error(f"Failed to load agent configs: {e}")
        return {}

AGENTS = load_agent_configs()

@app.post("/run/{agent_name}")
async def forward_to_agent(agent_name: str, request: Request):
    if agent_name not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent_config = AGENTS[agent_name]
    uds_path = agent_config["uds_path"]
    
    if not os.path.exists(uds_path):
        raise HTTPException(
            status_code=503,
            detail=f"Agent '{agent_name}' is not running (socket not found)"
        )
    
    try:
        data = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1/run",  # Dummy URL, actual communication is via UDS
                json={"data": data},
                transport=httpx.HTTPTransport(uds=uds_path)
            )
            return response.json()
    except Exception as e:
        logger.error(f"Error forwarding request to agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    return {
        "agents": [
            {
                "name": name,
                "status": "running" if os.path.exists(config["uds_path"]) else "stopped"
            }
            for name, config in AGENTS.items()
        ]
    } 