from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.database import get_db
from app.services import statistics_service
from app.schemas.statistics import StaffStatsOut, StaffStatsWithRankOut
from app.models.user import User, UserRole
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/statistics", tags=["Статистика"])

# Получение статистики персонала
@router.get("/", response_model=list[StaffStatsWithRankOut])
async def get_staff_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: date | None = Query(None, description="Фильтр: от даты (включительно)"),
    end_date: date | None = Query(None, description="Фильтр: до даты (включительно)"))  -> (list[StaffStatsOut] | dict):
    allowed_roles = {"Admin", "Barkeeper", "Cook", "Waiter"}
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    is_admin = current_user.role == UserRole.ADMIN

    stats = await statistics_service.get_staff_statistics(
        db,
        current_user.user_id,
        current_user.role,
        is_admin,
        start_date,
        end_date
    )

    return stats