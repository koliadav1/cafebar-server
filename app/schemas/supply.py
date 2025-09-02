from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.supply_orders import SupplyStatus

class SupplyOrderBase(BaseModel):
    ingredient_id: int
    ordered_quantity: Decimal = Field(max_digits=10, decimal_places=3)
    status: SupplyStatus = SupplyStatus.PENDING

class SupplyOrderCreate(SupplyOrderBase):
    price: float

class SupplyOrderUpdate(BaseModel):
    status: Optional[SupplyStatus] = None
    delivery_date: Optional[datetime] = None
    price: Optional[float] = None

class SupplyOrderOut(SupplyOrderBase):
    order_date: datetime
    supply_order_id: int
    delivery_date: Optional[datetime] = None
    price: float
    
    model_config = {
        "from_attributes": True
    }
