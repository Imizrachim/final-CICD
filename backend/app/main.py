"""Punto de entrada principal de la aplicación FastAPI (Task Manager Backend)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import init_db
from app.routers import health, tasks


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Espera disponibilidad de la base de datos e inicializa tablas al arrancar."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API REST para la gestión de tareas (Task Manager), "
        "preparada para pipelines CI/CD y despliegue en AWS ECS Fargate."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    _request: Request,
    _exc: SQLAlchemyError,
) -> JSONResponse:
    """Manejador global para errores inesperados de base de datos."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno en la base de datos."},
    )


app.include_router(health.router)
app.include_router(tasks.router)
