import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_unauthorized():
    response = client.post("/appointments/?doc_id=1&pat_id=1&time=2026-01-01T10:00:00")
    assert response.status_code == 401

def test_analytics():
    response = client.get("/analytics/")
    assert response.status_code == 200
    assert "total_appointments" in response.json()

def test_login_and_token():
    # Тестируем получение токена (это поднимет покрытие)
    response = client.post("/token", data={"username": "testuser", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()
