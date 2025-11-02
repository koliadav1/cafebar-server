from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from typing import List, Optional

from app.models.staff_shifts import StaffShift
from app.schemas.shift import StaffShiftCreate, StaffShiftUpdate

# Получить все смены
async def get_all_shifts(db: AsyncSession) -> List[StaffShift]:
    result = await db.execute(select(StaffShift))
    return result.scalars().all()

# Получить все активные смены на сейчас
async def get_active_shifts(db: AsyncSession) -> List[StaffShift]:
    result = await db.execute(
        select(StaffShift).where(StaffShift.is_active)
    )
    return result.scalars().all()

# Получить активную смену пользователя если есть
async def get_user_active_shift(db: AsyncSession, user_id: int) -> Optional[StaffShift]:
    result = await db.execute(
        select(StaffShift).where(
            and_(
                StaffShift.user_id == user_id,
                StaffShift.is_active
            )
        )
    )
    return result.scalar_one_or_none()

# Получить все смены на сегодня
async def get_today_shifts(db: AsyncSession) -> List[StaffShift]:
    today = date.today()
    result = await db.execute(
        select(StaffShift).where(StaffShift.shift_date == today)
    )
    return result.scalars().all()

# Получить будущие смены
async def get_future_shifts(db: AsyncSession) -> List[StaffShift]:
    result = await db.execute(
        select(StaffShift).where(StaffShift.is_future)
    )
    return result.scalars().all()

# Получить завершенные смены
async def get_past_shifts(db: AsyncSession) -> List[StaffShift]:
    result = await db.execute(
        select(StaffShift).where(StaffShift.is_past)
    )
    return result.scalars().all()

# Получить смены конкретного пользователя
async def get_shifts_by_user(db: AsyncSession, user_id: int) -> List[StaffShift]: 
    result = await db.execute(select(StaffShift).where(StaffShift.user_id == user_id))
    return result.scalars().all()

# Создать смену
async def create_shift(db: AsyncSession, shift: StaffShiftCreate) -> StaffShift:
    db_shift = StaffShift(**shift.model_dump())
    db.add(db_shift)
    await db.commit()
    await db.refresh(db_shift)
    return db_shift

# Изменить смену
async def update_shift(db: AsyncSession, shift_id: int, shift_data: StaffShiftUpdate) -> Optional[StaffShift]:
    result = await db.execute(select(StaffShift).where(StaffShift.shift_id == shift_id))
    db_shift = result.scalar_one_or_none()
    if not db_shift:
        return None
    for key, value in shift_data.model_dump().items():
        setattr(db_shift, key, value)
    await db.commit()
    await db.refresh(db_shift)
    return db_shift

# Удалить смену
async def delete_shift(db: AsyncSession, shift_id: int) -> bool:
    result = await db.execute(select(StaffShift).where(StaffShift.shift_id == shift_id))
    db_shift = result.scalar_one_or_none()
    if not db_shift:
        return False
    await db.delete(db_shift)
    await db.commit()
    return True