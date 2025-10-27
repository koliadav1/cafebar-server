import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.table_booking import TableBooking
from app.models.user import User
from app.realtime.websocket_manager import manager
from app.schemas.booking import (
    TableBookingCreate,
    TableBookingUpdate,
    TableBookingResponse,
    BookingStatus,
)
from app.services.auth_service import get_current_user
from app.services.booking_service import (
    create_booking,
    get_all_bookings,
    get_booking_by_id,
    get_bookings_by_user,
    get_bookings_by_status,
    update_booking,
    delete_booking,
)
from app.database import get_db

router = APIRouter(prefix="/bookings", tags=["Бронирование столиков"])

# Создание брони
@router.post("/", response_model=TableBookingResponse)
async def create_table_booking(data: TableBookingCreate, 
                               db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user)) -> TableBooking:
    if current_user.role not in ["Admin", "Client"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    booking = await create_booking(db, data)
    asyncio.create_task(manager.broadcast({
        "type": "reservation_create",
        "payload": {"action": "create", "booking": TableBookingResponse.model_validate(booking).model_dump()}
    }))
    return booking

# Получение бронирований
@router.get("/", response_model=List[TableBookingResponse])
async def get_bookings(user_id: Optional[int] = Query(None), 
                       status: Optional[BookingStatus] = Query(None), 
                       db: AsyncSession = Depends(get_db)) -> List[TableBooking]:
    if user_id is not None:
        return await get_bookings_by_user(db, user_id)
    elif status is not None:
        return await get_bookings_by_status(db, status)
    return await get_all_bookings(db)

# Получение брони по id
@router.get("/{booking_id}", response_model=TableBookingResponse)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)) -> TableBooking:
    booking = await get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    return booking

# Изменение брони по id
@router.put("/{booking_id}", response_model=TableBookingResponse)
async def update_table_booking(booking_id: int, data: TableBookingUpdate, 
                               db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user)) -> TableBooking:
    if current_user.role not in ["Admin", "Client"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    existing_booking = await get_booking_by_id(db, booking_id)
    if not existing_booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    if existing_booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Нельзя изменять завершенные и отмененные брони")

    booking = await update_booking(db, booking_id, data)

    asyncio.create_task(manager.broadcast({
        "type": "reservation_update",
        "payload": {"action": "update", "booking": TableBookingResponse.model_validate(booking).model_dump()}
    }))
    return booking

# Удаление брони по id
@router.delete("/{booking_id}")
async def delete_table_booking(booking_id: int, 
                               db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user)) -> dict[str, str]:
    if current_user.role not in ["Admin", "Client"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    success = await delete_booking(db, booking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    asyncio.create_task(manager.broadcast({
        "type": "reservation_delete",
        "payload": {"action": "delete", "booking_id": booking_id}
    }))
    return {"detail": "Бронь удалена"}