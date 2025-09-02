from enum import Enum
from sqlalchemy import Column, Integer, Numeric
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from app.database import Base

class OrderItemStatus(str, Enum):
    PENDING = 'Pending'
    IN_PROGRESS = 'In_progress'
    READY = 'Ready'
    COMPLETED = 'Completed'

class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    item_id = Column(Integer, ForeignKey('menu_items.item_id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Numeric, nullable=False)
    status = Column(SQLEnum(OrderItemStatus), nullable=False, default=OrderItemStatus.PENDING)

    order = relationship("Order", back_populates="items")