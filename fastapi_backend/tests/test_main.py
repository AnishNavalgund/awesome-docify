from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to awesome-docify API"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_hello():
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from awesome-docify API!"}
