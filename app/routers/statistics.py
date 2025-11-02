import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.database import get_db
from app.services import statistics_service
from app.schemas.statistics import StaffStatsWithRankOut, StaffStatsOut
from app.models.user import User, UserRole
from app.services.auth_service import get_current_user
from app.dependencies.cache import get_cache_manager, CacheManager

router = APIRouter(prefix="/statistics", tags=["Статистика"])

# Получение статистики персонала
@router.get("/", response_model=list[StaffStatsWithRankOut])
async def get_staff_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: date | None = Query(None, description="Фильтр: от даты (включительно)"),
    end_date: date | None = Query(None, description="Фильтр: до даты (включительно)"),
    cache: CacheManager = Depends(get_cache_manager)
) -> (list[StaffStatsOut] | dict):
    start_time = time.time()
    allowed_roles = {"Admin", "Barkeeper", "Cook", "Waiter"}
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    is_admin = current_user.role == UserRole.ADMIN

    cache_key = f"statistics:staff:user:{current_user.user_id}:admin:{is_admin}"
    if start_date:
        cache_key += f":start:{start_date}"
    if end_date:
        cache_key += f":end:{end_date}"

    if not is_admin and (not start_date or start_date == date.today()):
        cached_stats = await cache.get_cached(cache_key)
        if cached_stats:
            print(f"[REDIS] Staff statistics from cache (short TTL) - {time.time() - start_time:.3f}s")
            return cached_stats
        
        stats = await statistics_service.get_staff_statistics(
            db, current_user.user_id, current_user.role, is_admin, start_date, end_date
        )
        await cache.set_cached(cache_key, [item.model_dump() for item in stats], ttl=60)
        db_time = time.time() - start_time
        print(f"[REDIS] Staff statistics from database (short TTL) - {db_time:.3f}")

        return stats
    else:
        cached_stats = await cache.get_cached(cache_key)
        if cached_stats:
            print(f"[REDIS] Staff statistics from cache (long TTL) - {time.time() - start_time:.3f}s")
            return cached_stats
        
        stats = await statistics_service.get_staff_statistics(
            db, current_user.user_id, current_user.role, is_admin, start_date, end_date
        )
        db_time = time.time() - start_time
        print(f"[REDIS] Staff statistics from database (long TTL) - {db_time:.3f}")
        
        ttl = 300 if is_admin else 180
        await cache.set_cached(cache_key, [item.model_dump() for item in stats], ttl=ttl)
        return stats