"""Pruebas unitarias para el endpoint de salud (/health)."""

from collections.abc import Generator
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_health_endpoint_healthy(client: TestClient) -> None:
    """Verifica que /health responda 200 OK cuando la base de datos está activa."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["service"] == "task-manager-backend"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_health_endpoint_database_failure(client: TestClient) -> None:
    """Verifica que /health responda 503 cuando falla la conexión a la BD."""
    broken_session = MagicMock()
    broken_session.execute.side_effect = OperationalError(
        "SELECT 1",
        {},
        Exception("Connection refused"),
    )

    def override_broken_db() -> Generator[MagicMock, None, None]:
        yield broken_session

    app.dependency_overrides[get_db] = override_broken_db
    response = client.get("/health")
    assert response.status_code == 503
    assert "No se pudo establecer conexión" in response.json()["detail"]
