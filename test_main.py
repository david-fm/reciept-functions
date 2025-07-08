# test_main.py
import sys
import os

# Add the parent directory (where 'api' and 'main.py' reside) to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import pytest
from main import app
load_dotenv('.test.env')

# 'module' scope means it runs once for all tests in this file
@pytest.fixture(scope="module")
def client():
    # This 'with' statement makes the TestClient run your app's startup (lifespan) events
    with TestClient(app) as test_client:
        yield test_client  # This passes the test_client to your test functions

def test_login(client):
    print("USERNAME:", os.getenv("USERNAME"))
    response = client.post(
        "/auth/token",
        data={
            "username": os.getenv("USERNAME"),
            "password": os.getenv("PASSWORD")
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"



def test_receipt_upload(client):
    # First authenticate to get the token
    login_response = client.post(
        "/auth/token",
        data={
            "username": os.getenv("USERNAME"),
            "password": os.getenv("PASSWORD")
        }
    )
    with open("static/test_image.jpeg", "rb") as file:
        response = client.post(
            "/receipts/upload",
            files={"file": ("test_receipt.jpg", file, "image/jpeg")},
            headers={"Authorization": f"Bearer {login_response.json()['access_token']}"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    