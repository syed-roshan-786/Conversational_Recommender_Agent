import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_schema_validation():
    # Invalid request (missing messages)
    response = client.post("/chat", json={})
    assert response.status_code == 422
    
    # Valid minimal request
    response = client.post("/chat", json={"messages": [{"role": "user", "content": "hello"}]})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert "end_of_conversation" in data
