from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "MandoAI"}


def test_home_page_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "MandoAI" in response.text


def test_unknown_model_is_rejected():
    response = client.post(
        "/api/chat",
        json={"model": "not-a-model", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 400


def test_image_model_is_explicitly_unavailable():
    response = client.post(
        "/api/chat",
        json={"model": "glm-image", "messages": [{"role": "user", "content": "draw"}]},
    )
    assert response.status_code == 501
