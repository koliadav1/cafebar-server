from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum

from app.database import Base

class StaffRole(str, Enum):
    WAITER = 'Waiter'
    COOK = 'Cook'
    BARKEEPER = 'Barkeeper'

class OrderAssignment(Base):
    __tablename__ = "order_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role = Column(SQLEnum(StaffRole), nullable=False)

    order = relationship("Order", back_populates="assignments")
    user = relationship("User")