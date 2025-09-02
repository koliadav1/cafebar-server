from enum import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, ForeignKey, CheckConstraint
from datetime import datetime
from sqlalchemy.orm import relationship

from app.database import Base

class SupplyStatus(str, Enum):
    PENDING = 'Pending'
    DELIVERED = 'Delivered'
    CANCELLED = 'Cancelled'

class SupplyOrder(Base):
    __tablename__ = "supply_orders"
    __table_args__ = (
    CheckConstraint(
        "delivery_date IS NULL OR delivery_date >= order_date",
        name='check_delivery_date'
    ),
    CheckConstraint(
        "ordered_quantity > 0",
        name='check_positive_quantity'
    )
)

    supply_order_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.ingredient_id'), nullable=False)
    ordered_quantity = Column(Numeric(10, 3), nullable=False)  # 10 digits, 3 decimal places
    status = Column(SQLEnum(SupplyStatus), nullable=False, default=SupplyStatus.PENDING)
    order_date = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    delivery_date = Column(TIMESTAMP)
    price = Column(Numeric(10, 2), nullable=False)

    ingredient = relationship('Ingredient', back_populates='supply_orders')

    # Метод для проверки, является ли заказ просроченным
    @property
    def is_overdue(self):
        if self.delivery_date and self.status == SupplyStatus.PENDING:
            return datetime.now() > self.delivery_date
        return False