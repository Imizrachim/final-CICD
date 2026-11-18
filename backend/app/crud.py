"""Operaciones CRUD sobre la entidad Task utilizando SQLAlchemy."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Task, TaskStatus, utc_now
from app.schemas import TaskCreate, TaskStatusUpdate


def get_tasks(
    db: Session,
    status: TaskStatus | None = None,
) -> list[Task]:
    """Obtiene todas las tareas ordenadas de más reciente a más antigua."""
    stmt = select(Task)
    if status is not None:
        stmt = stmt.where(Task.status == status.value)
    stmt = stmt.order_by(Task.created_at.desc(), Task.id.desc())
    return list(db.scalars(stmt).all())


def get_task_by_id(db: Session, task_id: int) -> Task | None:
    """Obtiene una tarea por su identificador único."""
    stmt = select(Task).where(Task.id == task_id)
    return db.scalars(stmt).first()


def create_task(db: Session, task_in: TaskCreate) -> Task:
    """Crea y persiste una nueva tarea en la base de datos."""
    now = utc_now()
    db_task = Task(
        title=task_in.title,
        description=task_in.description or "",
        status=task_in.status.value,
        created_at=now,
        updated_at=now,
    )
    try:
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task
    except SQLAlchemyError:
        db.rollback()
        raise


def update_task_status(
    db: Session,
    db_task: Task,
    status_in: TaskStatusUpdate,
) -> Task:
    """Cambia el estado de una tarea existente (Pending o Completed)."""
    db_task.status = status_in.status.value
    db_task.updated_at = utc_now()
    try:
        db.commit()
        db.refresh(db_task)
        return db_task
    except SQLAlchemyError:
        db.rollback()
        raise


def delete_task(db: Session, db_task: Task) -> None:
    """Elimina permanentemente una tarea de la base de datos."""
    try:
        db.delete(db_task)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
