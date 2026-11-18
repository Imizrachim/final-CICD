"""Configuración y fixtures de Pytest para una base de datos de pruebas aislada."""

from collections.abc import Generator
import os
import socket
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import normalize_database_url
from app.database import Base, get_db, init_db
from app.main import app


def _is_tcp_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Comprueba rápidamente si un puerto TCP está aceptando conexiones."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def resolve_test_database_url() -> str:
    """Resuelve una base de datos de pruebas independiente de la de desarrollo."""
    explicit_url = os.getenv("TEST_DATABASE_URL")
    if explicit_url:
        normalized = normalize_database_url(explicit_url)
        if normalized.startswith("sqlite"):
            return normalized
        try:
            probe_engine = create_engine(
                normalized,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 2},
            )
            with probe_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            probe_engine.dispose()
            return normalized
        except OperationalError:
            pass

    if _is_tcp_port_open("127.0.0.1", 5432):
        default_pg_test_url = (
            "postgresql+psycopg://postgres:postgres@localhost:5432/taskmanager_test"
        )
        try:
            probe_engine = create_engine(
                default_pg_test_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 2},
            )
            with probe_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            probe_engine.dispose()
            return default_pg_test_url
        except OperationalError:
            pass

    return "sqlite://"


TEST_DB_URL = resolve_test_database_url()


def create_test_engine(db_url: str) -> Engine:
    """Crea el motor SQLAlchemy para la base de datos de pruebas independiente."""
    if db_url == "sqlite://":
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
        )
    return create_engine(db_url, pool_pre_ping=True)


test_engine = create_test_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Desactiva el umbral in-process cuando se ejecutan solo pruebas E2E o Smoke."""
    if not items:
        return
    all_external = all(
        "acceptance" in str(item.fspath) or "smoke" in str(item.fspath)
        for item in items
    )
    if all_external:
        if hasattr(config.option, "cov_fail_under"):
            config.option.cov_fail_under = 0
        cov_plugin = config.pluginmanager.get_plugin("_cov")
        if cov_plugin is not None and hasattr(cov_plugin, "options"):
            cov_plugin.options.cov_fail_under = 0


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Crea un esquema limpio en la BD de pruebas y entrega una sesión aislada."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente de pruebas FastAPI conectado exclusivamente a la BD de pruebas."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with patch(
        "app.main.init_db",
        side_effect=lambda: init_db(db_engine=test_engine),
    ):
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    app.dependency_overrides.clear()
