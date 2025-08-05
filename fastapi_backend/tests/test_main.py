from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Basic tests. In future, more detailed tests for functions and endpoints will be added!


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to awesome-docify API"}
