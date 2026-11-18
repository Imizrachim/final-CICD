"""Configuración centralizada de la aplicación mediante variables de entorno."""

import os
from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(raw_url: str) -> str:
    """Normaliza la URL de conexión para utilizar el driver psycopg (v3)."""
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


class Settings:
    """Contenedor de configuración del backend."""

    def __init__(self) -> None:
        raw_db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/taskmanager",
        )
        self.database_url: str = normalize_database_url(raw_db_url)
        self.app_name: str = os.getenv("APP_NAME", "Task Manager API")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.cors_origins: str = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,"
            "http://127.0.0.1:3000,http://127.0.0.1:5173",
        )
        self.db_max_retries: int = int(os.getenv("DB_MAX_RETRIES", "30"))
        self.db_retry_interval: float = float(os.getenv("DB_RETRY_INTERVAL", "2"))

    @property
    def cors_origins_list(self) -> list[str]:
        """Devuelve la lista de orígenes permitidos por CORS."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()
