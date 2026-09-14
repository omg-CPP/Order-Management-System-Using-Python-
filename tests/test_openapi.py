"""Swagger / OpenAPI surface matches the Five Circles docs pattern."""

from fastapi.testclient import TestClient

from app.main import app


def test_openapi_exposes_docs_and_core_paths():
    client = TestClient(app)

    docs = client.get("/docs")
    assert docs.status_code == 200

    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "Order Management System API"
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert "/api/v1/orders" in schema["paths"]
    assert "/api/v1/menu" in schema["paths"]
    assert "Orders" in {tag["name"] for tag in schema["tags"]}
    assert "Menu" in {tag["name"] for tag in schema["tags"]}


def test_root_health():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Order Management System API"
    assert body["status"] == "ok"
