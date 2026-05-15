import pytest
from fastapi.testclient import TestClient
from main import app, Base, engine, SessionLocal

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_full_workflow():
    # 1. Регистрация
    client.post("/users/register", params={"username": "testuser", "password": "password123"})
    
    # 2. Логин и получение токена
    login_res = client.post("/token", data={"username": "testuser", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Создание врача (позитивный сценарий)
    doc_res = client.post("/doctors/", params={"name": "Dr. House", "spec": "Diagnostic"}, headers=headers)
    assert doc_res.status_code == 200
    assert doc_res.json()["name"] == "Dr. House"

    # 4. Получение списка врачей (публичный эндпоинт)
    list_res = client.get("/doctors/")
    assert list_res.status_code == 200
    assert len(list_res.json()) > 0

def test_negative_scenarios():
    # 1. Попытка создать врача без токена (Задание 7: негативный сценарий)
    res = client.post("/doctors/", params={"name": "No Token", "spec": "None"})
    assert res.status_code == 401

    # 2. Запись к несуществующему врачу (Задание 2: валидация FK)
    client.post("/users/register", params={"username": "user2", "password": "pin"})
    token = client.post("/token", data={"username": "user2", "password": "pin"}).json()["access_token"]
    res = client.post("/appointments/", 
                      params={"doc_id": 999, "pat_id": 1, "time": "2026-05-15T10:00:00"}, 
                      headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    assert res.json()["detail"] == "No doctor/patient"