"""Endpoint de verificación de salud (Health Check) para Docker y AWS ECS."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import utc_now
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar el estado de salud del backend y la base de datos",
)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Comprueba que el servicio y la conexión con PostgreSQL estén operativos."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo establecer conexión con la base de datos.",
        ) from exc

    return HealthResponse(
        status="healthy",
        database="connected",
        service="task-manager-backend",
        version=settings.app_version,
        timestamp=utc_now(),
    )
