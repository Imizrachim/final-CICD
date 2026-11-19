"""Pruebas unitarias de configuración, espera de BD y manejo de errores CRUD."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app import crud
from app.config import Settings, normalize_database_url
from app.database import build_engine, get_db, init_db, wait_for_db
from app.main import app
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskStatusUpdate, TaskUpdate


def test_normalize_database_url_variants() -> None:
    """Verifica la normalización de URLs de conexión de PostgreSQL a psycopg v3."""
    assert normalize_database_url("postgres://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert normalize_database_url("postgresql://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert normalize_database_url("sqlite:///./test.db") == "sqlite:///./test.db"


def test_settings_cors_origins_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica que CORS_ORIGINS='*' devuelva la lista comodín ['*']."""
    monkeypatch.setenv("CORS_ORIGINS", "*")
    custom_settings = Settings()
    assert custom_settings.cors_origins_list == ["*"]


def test_build_engine_and_get_db_generator() -> None:
    """Verifica la creación de engine SQLite y el cierre de sesión en get_db."""
    temp_engine = build_engine("sqlite://")
    assert temp_engine is not None

    gen = get_db()
    session = next(gen)
    assert session is not None
    with pytest.raises(StopIteration):
        next(gen)


def test_wait_for_db_retries_and_succeeds() -> None:
    """Verifica que wait_for_db reintente cuando la BD tarda en iniciar."""
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    op_error = OperationalError("SELECT 1", {}, Exception("DB starting"))

    mock_engine.connect.side_effect = [op_error, mock_conn]

    with patch("app.database.time.sleep") as mock_sleep:
        wait_for_db(db_engine=mock_engine, max_retries=3, retry_interval=0.01)
        assert mock_engine.connect.call_count == 2
        mock_sleep.assert_called_once_with(0.01)


def test_wait_for_db_raises_after_max_retries() -> None:
    """Verifica que wait_for_db lance OperationalError tras agotar los intentos."""
    mock_engine = MagicMock()
    op_error = OperationalError("SELECT 1", {}, Exception("DB down"))
    mock_engine.connect.side_effect = op_error

    with patch("app.database.time.sleep"):
        with pytest.raises(OperationalError):
            wait_for_db(db_engine=mock_engine, max_retries=2, retry_interval=0.01)
    assert mock_engine.connect.call_count == 2


def test_init_db_and_app_lifespan() -> None:
    """Verifica que init_db y el ciclo de vida lifespan de FastAPI se ejecuten."""
    sqlite_engine = build_engine("sqlite://")
    init_db(db_engine=sqlite_engine)

    with patch("app.main.init_db") as mock_init_db:
        with TestClient(app):
            mock_init_db.assert_called_once()


def test_crud_rollbacks_on_sqlalchemy_error() -> None:
    """Verifica que cada operación de escritura haga rollback si ocurre un error SQL."""
    mock_session = MagicMock()
    mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
    sample_task = Task(
        id=1,
        title="Tarea",
        description="Desc",
        status=TaskStatus.PENDING.value,
    )

    with pytest.raises(SQLAlchemyError):
        crud.create_task(
            mock_session,
            TaskCreate(title="Nueva", description="Desc"),
        )
    assert mock_session.rollback.call_count == 1

    with pytest.raises(SQLAlchemyError):
        crud.update_task(
            mock_session,
            sample_task,
            TaskUpdate(title="Editada", description="Desc"),
        )
    assert mock_session.rollback.call_count == 2

    with pytest.raises(SQLAlchemyError):
        crud.update_task_status(
            mock_session,
            sample_task,
            TaskStatusUpdate(status=TaskStatus.COMPLETED),
        )
    assert mock_session.rollback.call_count == 3

    with pytest.raises(SQLAlchemyError):
        crud.delete_task(mock_session, sample_task)
    assert mock_session.rollback.call_count == 4
