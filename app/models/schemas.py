from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class Recommendation(BaseModel):
    name: str
    url: str
    test_type: Optional[str] = None
    reason: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation] = Field(default_factory=list)
    end_of_conversation: bool = False

class CatalogItem(BaseModel):
    name: str
    url: str
    description: str
    category: str
    skills_measured: List[str]
    duration: Optional[str] = None
    test_type: Optional[str] = None
    keywords: List[str]
