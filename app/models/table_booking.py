from enum import Enum
from sqlalchemy import CheckConstraint, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum

from app.database import Base

class BookingStatus(str, Enum):
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"

class TableBooking(Base):
    __tablename__ = "table_bookings"
    __table_args__ = (
        CheckConstraint('table_number > 0', name='check_positive_table'),
        CheckConstraint('duration_minutes > 0', name='check_positive_duration'),
    )

    booking_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_number = Column(Integer, nullable=False)
    booking_time = Column(DateTime, nullable=False)
    customer_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    status = Column(SQLEnum(BookingStatus), nullable=False, default=BookingStatus.CONFIRMED)
    duration_minutes = Column(Integer, default=120)