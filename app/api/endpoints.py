from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import chat_service

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Convert Pydantic models to dicts for the service
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    response = chat_service.process_chat(messages)
    return response
