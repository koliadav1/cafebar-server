from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.table_booking import TableBooking
from app.schemas.booking import TableBookingCreate, TableBookingUpdate

# Создание брони
async def create_booking(db: AsyncSession, booking_data: TableBookingCreate) -> TableBooking:
    booking = TableBooking(**booking_data.model_dump())
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking

# Получение брони по id
async def get_booking_by_id(db: AsyncSession, booking_id: int) -> Optional[TableBooking]:
    result = await db.execute(select(TableBooking).where(TableBooking.booking_id == booking_id))
    return result.scalar_one_or_none()

# Получение всех бронирований
async def get_all_bookings(db: AsyncSession) -> List[TableBooking]:
    result = await db.execute(select(TableBooking))
    return result.scalars().all()

# Получение бронирований конкретного пользователя
async def get_bookings_by_user(db: AsyncSession, user_id: int) -> List[TableBooking]:
    result = await db.execute(select(TableBooking).where(TableBooking.user_id == user_id))
    return result.scalars().all()

# Получение бронирований в зависимости от их статуса
async def get_bookings_by_status(db: AsyncSession, status: str) -> List[TableBooking]:
    result = await db.execute(select(TableBooking).where(TableBooking.status == status))
    return result.scalars().all()

# Изменение бронирования
async def update_booking(db: AsyncSession, booking_id: int, update_data: TableBookingUpdate) -> Optional[TableBooking]:
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        return None
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(booking, field, value)
    await db.commit()
    await db.refresh(booking)
    return booking

# Удаление бронирования
async def delete_booking(db: AsyncSession, booking_id: int) -> bool:
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        return False
    await db.delete(booking)
    await db.commit()
    return True