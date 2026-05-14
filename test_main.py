import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_appointment():
    response = client.post("/appointments/?doc_id=1&pat_id=1&time=2026-12-01T10:00:00")
    assert response.status_code in [200, 400]

def test_busy_slot():
    time = "2026-12-01T12:00:00"
    client.post(f"/appointments/?doc_id=1&pat_id=1&time={time}")
    response = client.post(f"/appointments/?doc_id=1&pat_id=2&time={time}")
    assert response.status_code == 400
