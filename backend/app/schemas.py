"""Esquemas Pydantic para validación de entrada y serialización de salida."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskStatus


class TaskBase(BaseModel):
    """Atributos comunes y validaciones para creación de tareas."""

    title: str = Field(
        ...,
        max_length=150,
        description="Título descriptivo de la tarea.",
    )
    description: str | None = Field(
        default="",
        max_length=1000,
        description="Descripción detallada de la tarea.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        """Evita títulos vacíos o compuestos únicamente por espacios en blanco."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El título de la tarea no puede estar vacío.")
        return cleaned

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str:
        """Normaliza la descripción asegurando una cadena limpia."""
        if value is None:
            return ""
        return value.strip()


class TaskCreate(TaskBase):
    """Esquema para crear una nueva tarea."""

    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Estado inicial de la tarea (Pending o Completed).",
    )


class TaskStatusUpdate(BaseModel):
    """Esquema para actualizar exclusivamente el estado de una tarea."""

    status: TaskStatus = Field(
        ...,
        description="Nuevo estado de la tarea (Pending o Completed).",
    )


class TaskResponse(BaseModel):
    """Esquema de respuesta de una tarea."""

    id: int
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeleteTaskResponse(BaseModel):
    """Esquema de confirmación tras eliminar una tarea."""

    message: str
    id: int


class HealthResponse(BaseModel):
    """Esquema de respuesta para el endpoint de salud."""

    status: str
    database: str
    service: str
    version: str
    timestamp: datetime
