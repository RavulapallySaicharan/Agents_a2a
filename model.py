from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Optional
from datetime import datetime

class QueryRequest(BaseModel):
    userInput: str
    sessionID: UUID

class DataFrameRequest(BaseModel):
    userInput: str
    sessionID: UUID
    dataframe: Optional[Dict] = None  # JSON representation of DataFrame

class Text2SQLRequest(BaseModel):
    userInput: str
    sessionID: UUID
    schema: Optional[str] = None  # Database schema information

class ConversationEntry(BaseModel):
    timestamp: datetime
    userInput: str
    response: dict
    agentType: str

class AgentResponse(BaseModel):
    session_id: UUID
    agent: str
    confidence: float
    response: dict 