from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.table_booking import TableBooking
from app.schemas.booking import TableBookingCreate, TableBookingUpdate

#Создание брони
def create_booking(db: Session, booking_data: TableBookingCreate) -> TableBooking:
    booking = TableBooking(**booking_data.dict())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

#Получение брони по id
def get_booking_by_id(db: Session, booking_id: int) -> Optional[TableBooking]:
    return db.query(TableBooking).filter(TableBooking.booking_id == booking_id).first()

#Получение всех бронирований
def get_all_bookings(db: Session) -> List[TableBooking]:
    return db.query(TableBooking).all()

#Получение бронирований конкретного пользователя
def get_bookings_by_user(db: Session, user_id: int) -> List[TableBooking]:
    return db.query(TableBooking).filter(TableBooking.user_id == user_id).all()

#Получение бронирований в зависимости от их статуса
def get_bookings_by_status(db: Session, status: str) -> List[TableBooking]:
    return db.query(TableBooking).filter(TableBooking.status == status).all()

#Изменение бронирования
def update_booking(db: Session, booking_id: int, update_data: TableBookingUpdate) -> Optional[TableBooking]:
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return None
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(booking, field, value)
    db.commit()
    db.refresh(booking)
    return booking

#Удаление бронирования
def delete_booking(db: Session, booking_id: int) -> bool:
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return False
    db.delete(booking)
    db.commit()
    return True
