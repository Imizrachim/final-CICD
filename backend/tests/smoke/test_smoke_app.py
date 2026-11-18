"""Suite de pruebas Smoke para verificar salud, versión y API tras el despliegue."""

import os
import uuid
import pytest
import requests
from fastapi.testclient import TestClient


@pytest.mark.smoke
def test_smoke_health_and_version(client: TestClient) -> None:
    """Verifica que /health responda 200 OK, healthy y coincida con EXPECTED_VERSION."""
    base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
    expected_version = os.getenv("EXPECTED_VERSION")

    if base_url:
        response = requests.get(f"{base_url}/health", timeout=10)
    else:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["database"] == "connected"
    assert "version" in payload

    if expected_version:
        assert payload["version"] == expected_version


@pytest.mark.smoke
def test_smoke_tasks_critical_path(client: TestClient) -> None:
    """Verifica que el listado, creación y eliminación básica de tareas respondan."""
    base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
    smoke_title = f"Smoke Test Task {uuid.uuid4().hex[:6]}"
    task_payload = {
        "title": smoke_title,
        "description": "Verificación automática posdespliegue",
    }

    if base_url:
        list_res = requests.get(f"{base_url}/api/tasks", timeout=10)
        assert list_res.status_code == 200

        create_res = requests.post(
            f"{base_url}/api/tasks",
            json=task_payload,
            timeout=10,
        )
        assert create_res.status_code == 201
        task_id = create_res.json()["id"]

        delete_res = requests.delete(f"{base_url}/api/tasks/{task_id}", timeout=10)
        assert delete_res.status_code == 200
    else:
        list_res = client.get("/api/tasks")
        assert list_res.status_code == 200

        create_res = client.post("/api/tasks", json=task_payload)
        assert create_res.status_code == 201
        task_id = create_res.json()["id"]

        delete_res = client.delete(f"/api/tasks/{task_id}")
        assert delete_res.status_code == 200
