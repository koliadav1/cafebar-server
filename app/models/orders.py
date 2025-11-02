from enum import Enum
from sqlalchemy import CheckConstraint, Enum as SQLEnum, Text
from sqlalchemy import Column, Integer, Numeric, TIMESTAMP
from sqlalchemy import ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship

from app.database import Base

class OrderStatus(str, Enum):
    PENDING = 'Pending'
    IN_PROGRESS = 'In_progress'
    READY = 'Ready'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    order_date = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    table_number = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)

    items = relationship("OrderItem", back_populates="order")
    assignments = relationship("OrderAssignment", back_populates="order", cascade="all, delete-orphan")


__table_args__ = (
    CheckConstraint(
        "(status = 'Completed'::orderstatus AND total_price > 0) OR (status != 'Completed'::orderstatus)",
        name='check_completed_order_price'
    ),
)