"""Configuración de conexión a la base de datos y gestión de sesiones SQLAlchemy."""

import logging
import time
from collections.abc import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Clase base declarativa para los modelos ORM."""


def build_engine(database_url: str) -> Engine:
    """Crea una instancia de Engine de SQLAlchemy según el motor configurado."""
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    return create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Provee una sesión de base de datos transaccional por solicitud HTTP."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(
    db_engine: Engine | None = None,
    max_retries: int | None = None,
    retry_interval: float | None = None,
) -> None:
    """Espera a que la base de datos esté disponible antes de iniciar operaciones."""
    target_engine = db_engine or engine
    retries = max_retries if max_retries is not None else settings.db_max_retries
    interval = (
        retry_interval if retry_interval is not None else settings.db_retry_interval
    )

    last_error: OperationalError | None = None
    for attempt in range(1, retries + 1):
        try:
            with target_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Conexión con la base de datos establecida correctamente.")
            return
        except OperationalError as exc:
            last_error = exc
            logger.warning(
                "Base de datos no disponible (intento %d/%d). Reintentando en %ss...",
                attempt,
                retries,
                interval,
            )
            if attempt < retries:
                time.sleep(interval)

    if last_error is not None:
        raise last_error


def init_db(db_engine: Engine | None = None) -> None:
    """Verifica disponibilidad y crea las tablas en la base de datos."""
    target_engine = db_engine or engine
    wait_for_db(db_engine=target_engine)
    Base.metadata.create_all(bind=target_engine)
