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


def test_model_catalog_contains_only_glm_text_models():
    response = client.get("/api/models")
    assert response.status_code == 200
    models = response.json()["models"]
    assert models
    assert all(item["provider"] == "GLM" for item in models)
    assert all(item["id"].startswith("glm-") for item in models)
    assert "provider-openai" not in {item["id"] for item in models}


def test_removed_provider_models_are_rejected():
    for model in ("provider-openai", "ling-3.0-flash", "gpt-5.4-mini"):
        response = client.post(
            "/api/chat",
            json={"model": model, "messages": [{"role": "user", "content": "hello"}]},
        )
        assert response.status_code == 400
