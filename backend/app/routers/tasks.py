"""Endpoints REST para la gestión de tareas."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import Task, TaskStatus
from app.schemas import (
    DeleteTaskResponse,
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def _get_existing_task_or_404(db: Session, task_id: int) -> Task:
    """Busca una tarea por ID o lanza HTTP 404 si no existe."""
    db_task = crud.get_task_by_id(db, task_id)
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La tarea con ID {task_id} no existe.",
        )
    return db_task


@router.get(
    "",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener todas las tareas",
)
def list_tasks(
    task_status: TaskStatus | None = Query(
        default=None,
        alias="status",
        description="Filtrar opcionalmente por estado (Pending o Completed).",
    ),
    db: Session = Depends(get_db),
) -> list[Task]:
    """Devuelve el listado de tareas registradas, con filtro opcional por estado."""
    return crud.get_tasks(db, status=task_status)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una tarea específica por ID",
)
def get_task(
    task_id: int = Path(..., ge=1, description="Identificador único de la tarea"),
    db: Session = Depends(get_db),
) -> Task:
    """Devuelve el detalle de una tarea específica."""
    return _get_existing_task_or_404(db, task_id)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva tarea",
)
def create_new_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
) -> Task:
    """Registra una nueva tarea con título y descripción validados."""
    return crud.create_task(db, task_in)


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Cambiar el estado de una tarea",
)
def change_task_status(
    status_in: TaskStatusUpdate,
    task_id: int = Path(..., ge=1, description="Identificador único de la tarea"),
    db: Session = Depends(get_db),
) -> Task:
    """Actualiza el estado de una tarea entre Pending y Completed."""
    db_task = _get_existing_task_or_404(db, task_id)
    return crud.update_task_status(db, db_task, status_in)


@router.delete(
    "/{task_id}",
    response_model=DeleteTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar una tarea existente",
)
def remove_task(
    task_id: int = Path(..., ge=1, description="Identificador único de la tarea"),
    db: Session = Depends(get_db),
) -> DeleteTaskResponse:
    """Elimina una tarea de la base de datos."""
    db_task = _get_existing_task_or_404(db, task_id)
    crud.delete_task(db, db_task)
    return DeleteTaskResponse(
        message="Tarea eliminada correctamente.",
        id=task_id,
    )
