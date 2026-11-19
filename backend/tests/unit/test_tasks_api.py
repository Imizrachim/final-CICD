"""Pruebas unitarias para los endpoints REST de tareas (/api/tasks)."""

from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError


def test_create_task_success(client: TestClient) -> None:
    """Verifica la creación exitosa de una tarea con datos válidos."""
    payload = {
        "title": "Configurar pipeline CI",
        "description": "Agregar etapas de Flake8, Pylint, Black y Pytest-Cov",
    }
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] >= 1
    assert data["title"] == "Configurar pipeline CI"
    assert data["description"] == (
        "Agregar etapas de Flake8, Pylint, Black y Pytest-Cov"
    )
    assert data["status"] == "Pending"
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_trims_whitespace_and_handles_null_description(
    client: TestClient,
) -> None:
    """Verifica que el título y la descripción se limpien correctamente."""
    payload = {"title": "   Tarea con espacios   ", "description": None}
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea con espacios"
    assert data["description"] == ""
    assert data["status"] == "Pending"


def test_get_all_tasks_and_filter_by_status(client: TestClient) -> None:
    """Verifica la consulta de todas las tareas y el filtrado por estado."""
    client.post(
        "/api/tasks",
        json={"title": "Tarea Pendiente 1", "description": "Desc 1"},
    )
    client.post(
        "/api/tasks",
        json={
            "title": "Tarea Completada 1",
            "description": "Desc 2",
            "status": "Completed",
        },
    )

    all_res = client.get("/api/tasks")
    assert all_res.status_code == 200
    assert len(all_res.json()) == 2

    pending_res = client.get("/api/tasks?status=Pending")
    assert pending_res.status_code == 200
    pending_tasks = pending_res.json()
    assert len(pending_tasks) == 1
    assert pending_tasks[0]["title"] == "Tarea Pendiente 1"

    completed_res = client.get("/api/tasks?status=Completed")
    assert completed_res.status_code == 200
    completed_tasks = completed_res.json()
    assert len(completed_tasks) == 1
    assert completed_tasks[0]["title"] == "Tarea Completada 1"


def test_get_task_by_id_success(client: TestClient) -> None:
    """Verifica la consulta de una tarea específica mediante su ID."""
    create_res = client.post(
        "/api/tasks",
        json={"title": "Consultar tarea", "description": "Detalle específico"},
    )
    task_id = create_res.json()["id"]

    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == task_id
    assert data["title"] == "Consultar tarea"
    assert data["description"] == "Detalle específico"


def test_update_task_success(client: TestClient) -> None:
    """Verifica la actualización completa (PUT) de una tarea existente."""
    create_res = client.post(
        "/api/tasks",
        json={"title": "Título original", "description": "Descripción original"},
    )
    task_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Título actualizado",
            "description": "Descripción actualizada",
            "status": "Completed",
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Título actualizado"
    assert updated["description"] == "Descripción actualizada"
    assert updated["status"] == "Completed"


def test_change_task_status_patch(client: TestClient) -> None:
    """Verifica el cambio de estado mediante PATCH /api/tasks/{id}/status."""
    create_res = client.post(
        "/api/tasks",
        json={"title": "Cambiar estado", "description": "Probar PATCH"},
    )
    task_id = create_res.json()["id"]
    assert create_res.json()["status"] == "Pending"

    patch_completed = client.patch(
        f"/api/tasks/{task_id}/status",
        json={"status": "Completed"},
    )
    assert patch_completed.status_code == 200
    assert patch_completed.json()["status"] == "Completed"

    patch_pending = client.patch(
        f"/api/tasks/{task_id}/status",
        json={"status": "Pending"},
    )
    assert patch_pending.status_code == 200
    assert patch_pending.json()["status"] == "Pending"


def test_delete_task_success(client: TestClient) -> None:
    """Verifica la eliminación de una tarea y que ya no pueda consultarse."""
    create_res = client.post(
        "/api/tasks",
        json={"title": "Tarea a eliminar", "description": "Temporal"},
    )
    task_id = create_res.json()["id"]

    delete_res = client.delete(f"/api/tasks/{task_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["id"] == task_id

    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 404


def test_validation_rejects_invalid_data(client: TestClient) -> None:
    """Verifica que el backend rechace títulos vacíos y datos incorrectos (422)."""
    empty_title = client.post(
        "/api/tasks",
        json={"title": "", "description": "Sin título"},
    )
    assert empty_title.status_code == 422

    whitespace_title = client.post(
        "/api/tasks",
        json={"title": "     ", "description": "Solo espacios"},
    )
    assert whitespace_title.status_code == 422

    too_long_title = client.post(
        "/api/tasks",
        json={"title": "A" * 151, "description": "Excede límite"},
    )
    assert too_long_title.status_code == 422

    invalid_status = client.post(
        "/api/tasks",
        json={"title": "Tarea", "status": "InProgress"},
    )
    assert invalid_status.status_code == 422

    invalid_id = client.get("/api/tasks/0")
    assert invalid_id.status_code == 422


def test_non_existent_task_returns_404(client: TestClient) -> None:
    """Verifica el manejo de tareas inexistentes en todos los endpoints por ID."""
    missing_id = 99999

    assert client.get(f"/api/tasks/{missing_id}").status_code == 404
    assert (
        client.put(
            f"/api/tasks/{missing_id}",
            json={"title": "No existe", "description": ""},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/tasks/{missing_id}/status",
            json={"status": "Completed"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/tasks/{missing_id}").status_code == 404


def test_global_sqlalchemy_error_handler_returns_500(client: TestClient) -> None:
    """Verifica que un fallo inesperado de base de datos devuelva HTTP 500 limpio."""
    with patch(
        "app.routers.tasks.crud.get_tasks",
        side_effect=SQLAlchemyError("Simulated DB crash"),
    ):
        response = client.get("/api/tasks")
        assert response.status_code == 500
        assert response.json() == {"detail": "Error interno en la base de datos."}
