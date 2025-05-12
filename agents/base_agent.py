from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

class AgentRequest(BaseModel):
    data: Dict[str, Any]

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.app = FastAPI(title=f"{name} Agent")
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.post("/run")
        async def run_agent(request: AgentRequest):
            try:
                result = await self.process_request(request.data)
                return {"status": "success", "result": result}
            except Exception as e:
                logging.error(f"Error in agent {self.name}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override this method in your agent implementation
        """
        raise NotImplementedError("Subclasses must implement process_request method") 