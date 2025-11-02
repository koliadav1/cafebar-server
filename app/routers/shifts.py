import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.dependencies.cache import CacheManager, get_cache_manager
from app.models.staff_shifts import StaffShift
from app.database import get_db
from app.models.user import User
from app.schemas.shift import StaffShiftOut, StaffShiftCreate, StaffShiftUpdate
from app.services import shift_service
from app.realtime.websocket_manager import manager
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/shifts",
    tags=["Смены"]
)

# Получение смен
@router.get("/", response_model=List[StaffShiftOut])
async def get_all_shifts(db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         cache: CacheManager = Depends(get_cache_manager)) -> List[StaffShift]:
    allowed_roles = {"Admin", "Barkeeper", "Cook", "Waiter"}
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    start_time = time.time()
    cache_key = f"shifts:user:{current_user.user_id}:role:{current_user.role}"
    
    cached_shifts = await cache.get_cached(cache_key)
    if cached_shifts:
        print(f"[REDIS] Shifts from cache - {time.time() - start_time:.3f}s")
        return cached_shifts
    
    if current_user.role == "Admin":
        shifts = await shift_service.get_all_shifts(db)
    else:
        shifts = await shift_service.get_shifts_by_user(db, current_user.user_id)
    db_time = time.time() - start_time
    print(f"[REDIS] Shifts from database - {db_time:.3f}s")

    shifts_out = [StaffShiftOut.model_validate(shift) for shift in shifts]
    await cache.set_cached(cache_key, [shift.model_dump() for shift in shifts_out], ttl=300)
    
    return shifts_out


# Получить все активные смены на текущий момент
@router.get("/active", response_model=List[StaffShiftOut])
async def get_active_shifts(db: AsyncSession = Depends(get_db), 
                            current_user: User = Depends(get_current_user),
                            cache: CacheManager = Depends(get_cache_manager)) -> List[StaffShift]:
    if current_user.role not in {"Admin", "Barkeeper", "Cook", "Waiter"}:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    start_time = time.time()
    cache_key = "shifts:active:current"
    
    cached_shifts = await cache.get_cached(cache_key)
    if cached_shifts:
        print(f"[REDIS] Active shifts from cache - {time.time() - start_time:.3f}s")
        return cached_shifts

    shifts = await shift_service.get_active_shifts(db)
    db_time = time.time() - start_time
    print(f"[REDIS] Active shifts from database - {db_time:.3f}s")
    
    shifts_out = [StaffShiftOut.model_validate(shift) for shift in shifts]
    await cache.set_cached(cache_key, [shift.model_dump() for shift in shifts_out], ttl=60)
    
    return shifts_out 

# Получить все смены на сегодня
@router.get("/today", response_model=List[StaffShiftOut])
async def get_today_shifts(db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user),
                           cache: CacheManager = Depends(get_cache_manager)) -> List[StaffShift]:
    if current_user.role not in {"Admin", "Barkeeper", "Cook", "Waiter"}:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    start_time = time.time()
    cache_key = "shifts:today"
    
    cached_shifts = await cache.get_cached(cache_key)
    if cached_shifts:
        print(f"[REDIS] Today shifts from cache - {time.time() - start_time:.3f}s")
        return cached_shifts

    shifts = await shift_service.get_today_shifts(db)
    db_time = time.time() - start_time
    print(f"[REDIS] Today shifts from database - {db_time:.3f}s")
    
    shifts_out = [StaffShiftOut.model_validate(shift) for shift in shifts]
    await cache.set_cached(cache_key, [shift.model_dump() for shift in shifts_out], ttl=300)
    
    return shifts_out

# Получить будущие смены
@router.get("/future", response_model=List[StaffShiftOut])
async def get_future_shifts(db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user),
                            cache: CacheManager = Depends(get_cache_manager)) -> List[StaffShift]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут просматривать будущие смены")
    start_time = time.time()
    cache_key = "shifts:future"
    
    cached_shifts = await cache.get_cached(cache_key)
    if cached_shifts:
        print(f"[REDIS] Future shifts from cache - {time.time() - start_time:.3f}s")
        return cached_shifts

    shifts = await shift_service.get_future_shifts(db)
    db_time = time.time() - start_time
    print(f"[REDIS] Future shifts from database - {db_time:.3f}s")
    
    shifts_out = [StaffShiftOut.model_validate(shift) for shift in shifts]
    await cache.set_cached(cache_key, [shift.model_dump() for shift in shifts_out], ttl=600)
    
    return shifts_out

# Получить завершенные смены
@router.get("/past", response_model=List[StaffShiftOut])
async def get_past_shifts(db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user),
                          cache: CacheManager = Depends(get_cache_manager)) -> List[StaffShift]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут просматривать историю смен")
    start_time = time.time()
    cache_key = "shifts:past"
    
    cached_shifts = await cache.get_cached(cache_key)
    if cached_shifts:
        print(f"[REDIS] Past shifts from cache - {time.time() - start_time:.3f}s")
        return cached_shifts

    shifts = await shift_service.get_past_shifts(db)
    db_time = time.time() - start_time
    print(f"[REDIS] Past shifts from database - {db_time:.3f}s")
    
    shifts_out = [StaffShiftOut.model_validate(shift) for shift in shifts]
    await cache.set_cached(cache_key, [shift.model_dump() for shift in shifts_out], ttl=1800)
    
    return shifts_out

# Получение смен конкретного пользователя
@router.get("/user/{user_id}", response_model=List[StaffShiftOut])
async def get_shifts_by_user(user_id: int, 
                             db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(get_current_user),
                             cache: CacheManager = Depends(get_cache_manager)) -> List[StaffShift]:
    if current_user.role not in {"Admin", "Barkeeper", "Cook", "Waiter"}:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    start_time = time.time()
    cache_key = f"shifts:user:{user_id}:all"
    
    cached_shifts = await cache.get_cached(cache_key)
    if cached_shifts:
        print(f"[REDIS] User shifts from cache - {time.time() - start_time:.3f}s")
        return cached_shifts

    shifts = await shift_service.get_shifts_by_user(db, user_id)
    db_time = time.time() - start_time
    print(f"[REDIS] User shifts from database - {db_time:.3f}s")
    
    shifts_out = [StaffShiftOut.model_validate(shift) for shift in shifts]
    await cache.set_cached(cache_key, [shift.model_dump() for shift in shifts_out], ttl=600)
    
    return shifts_out

# Создание смены
@router.post("/", response_model=StaffShiftOut)
async def create_shift(shift: StaffShiftCreate, 
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       cache: CacheManager = Depends(get_cache_manager)) -> StaffShift:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_shift = await shift_service.create_shift(db, shift)
    new_shift_out = StaffShiftOut.model_validate(new_shift)
    await cache.invalidate_pattern("shifts:*")
    asyncio.create_task(manager.broadcast({
        "type": "shift_create",
        "payload": {"action": "create", "shift": StaffShiftOut.model_validate(new_shift).model_dump()}
    }))
    return new_shift_out

# Изменение смены
@router.put("/{shift_id}", response_model=StaffShiftOut)
async def update_shift(shift_id: int, 
                       shift: StaffShiftUpdate, 
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       cache: CacheManager = Depends(get_cache_manager)) -> StaffShift:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    updated_shift = await shift_service.update_shift(db, shift_id, shift)
    if not updated_shift:
        raise HTTPException(status_code=404, detail="Смена не найдена")
    updated_shift_out = StaffShiftOut.model_validate(updated_shift)
    await cache.invalidate_pattern("shifts:*")
    asyncio.create_task(manager.broadcast({
        "type": "shift_update",
        "payload": {"action": "update", "shift": StaffShiftOut.model_validate(updated_shift).model_dump()}
    }))
    return updated_shift_out

# Удаление смены
@router.delete("/{shift_id}")
async def delete_shift(shift_id: int, 
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       cache: CacheManager = Depends(get_cache_manager)) -> dict[str, str]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    success = await shift_service.delete_shift(db, shift_id)
    if not success:
        raise HTTPException(status_code=404, detail="Смена не найдена")
    await cache.invalidate_pattern("shifts:*")
    asyncio.create_task(manager.broadcast({
        "type": "shift_delete",
        "payload": {"action": "delete", "shift_id": shift_id}
    }))
    return {"detail": "Смена удалена"}