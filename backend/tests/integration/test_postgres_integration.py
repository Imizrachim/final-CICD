"""Pruebas de integración entre el backend FastAPI/SQLAlchemy y la base de datos."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskStatusUpdate, TaskUpdate
from tests.conftest import TestingSessionLocal, test_engine


@pytest.mark.integration
def test_database_connection_and_schema_creation(db_session: Session) -> None:
    """Valida la conexión activa a la base de datos y la creación de la tabla tasks."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    assert "tasks" in tables

    columns = {col["name"] for col in inspector.get_columns("tasks")}
    expected_columns = {
        "id",
        "title",
        "description",
        "status",
        "created_at",
        "updated_at",
    }
    assert expected_columns.issubset(columns)


@pytest.mark.integration
def test_database_persistence_across_sessions(db_session: Session) -> None:
    """Valida que los registros creados persistan entre sesiones independientes."""
    created = crud.create_task(
        db_session,
        TaskCreate(
            title="Persistencia en PostgreSQL",
            description="Verificar lectura desde otra sesión transaccional",
            status=TaskStatus.PENDING,
        ),
    )
    assert created.id is not None

    with TestingSessionLocal() as second_session:
        fetched = crud.get_task_by_id(second_session, created.id)
        assert fetched is not None
        assert fetched.title == "Persistencia en PostgreSQL"
        assert (
            fetched.description == "Verificar lectura desde otra sesión transaccional"
        )
        assert fetched.status == TaskStatus.PENDING.value


@pytest.mark.integration
def test_database_crud_lifecycle_and_filters(db_session: Session) -> None:
    """Valida creación, consulta, edición, cambio de estado y eliminación en BD."""
    task_a = crud.create_task(
        db_session,
        TaskCreate(title="Tarea Integración A", description="Pendiente inicial"),
    )
    task_b = crud.create_task(
        db_session,
        TaskCreate(
            title="Tarea Integración B",
            description="Completada inicial",
            status=TaskStatus.COMPLETED,
        ),
    )

    all_tasks = crud.get_tasks(db_session)
    assert len(all_tasks) == 2

    pending_only = crud.get_tasks(db_session, status=TaskStatus.PENDING)
    assert len(pending_only) == 1
    assert pending_only[0].id == task_a.id

    completed_only = crud.get_tasks(db_session, status=TaskStatus.COMPLETED)
    assert len(completed_only) == 1
    assert completed_only[0].id == task_b.id

    updated_a = crud.update_task(
        db_session,
        task_a,
        TaskUpdate(
            title="Tarea Integración A Editada",
            description="Descripción modificada en BD",
        ),
    )
    assert updated_a.title == "Tarea Integración A Editada"
    assert updated_a.description == "Descripción modificada en BD"
    assert updated_a.updated_at >= updated_a.created_at

    toggled_a = crud.update_task_status(
        db_session,
        updated_a,
        TaskStatusUpdate(status=TaskStatus.COMPLETED),
    )
    assert toggled_a.status == TaskStatus.COMPLETED.value

    crud.delete_task(db_session, toggled_a)
    assert crud.get_task_by_id(db_session, task_a.id) is None
    assert len(crud.get_tasks(db_session)) == 1


@pytest.mark.integration
def test_database_constraints_and_transaction_rollback(
    db_session: Session,
) -> None:
    """Valida que violaciones NOT NULL hagan rollback y mantengan la sesión sana."""
    invalid_record = Task(description="Violación NOT NULL")
    invalid_record.title = None  # type: ignore[assignment]
    db_session.add(invalid_record)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    valid_task = crud.create_task(
        db_session,
        TaskCreate(title="Tarea posterior a rollback", description="Sesión sana"),
    )
    assert valid_task.id is not None
    assert len(crud.get_tasks(db_session)) == 1


@pytest.mark.integration
def test_api_to_database_full_integration_flow(
    client: TestClient,
    db_session: Session,
) -> None:
    """Valida el flujo completo HTTP -> FastAPI -> SQLAlchemy -> Base de datos."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["database"] == "connected"

    post_res = client.post(
        "/api/tasks",
        json={
            "title": "Desplegar en ECS Fargate",
            "description": "Configurar servicio e imagen en ECR",
        },
    )
    assert post_res.status_code == 201
    task_id = post_res.json()["id"]

    db_record = crud.get_task_by_id(db_session, task_id)
    assert db_record is not None
    assert db_record.title == "Desplegar en ECS Fargate"

    put_res = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Desplegar en AWS ECS Fargate",
            "description": "Imagen publicada en Amazon ECR",
        },
    )
    assert put_res.status_code == 200

    patch_res = client.patch(
        f"/api/tasks/{task_id}/status",
        json={"status": "Completed"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Completed"

    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "Completed"

    invalid_res = client.post("/api/tasks", json={"title": "   "})
    assert invalid_res.status_code == 422

    del_res = client.delete(f"/api/tasks/{task_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/tasks/{task_id}").status_code == 404
