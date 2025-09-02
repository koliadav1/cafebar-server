from datetime import datetime
from pydantic import BaseModel
from typing import List

from app.models.order_assignments import StaffRole
from app.models.orders import OrderStatus
from app.models.order_items import OrderItemStatus

class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int
    price: float

class OrderCreate(BaseModel):
    user_id: int
    table_number: int
    items: List[OrderItemCreate]
    comment: str | None = None

class OrderItemOut(BaseModel):
    item_id: int
    quantity: int
    price: float
    status: OrderItemStatus
    order_item_id: int
    
    model_config = {
        "from_attributes": True
    }

class OrderOut(BaseModel):
    order_id: int
    user_id: int
    table_number: int
    total_price: float
    order_date: datetime
    status: OrderStatus
    items: List[OrderItemOut]
    comment: str | None = None

    model_config = {
        "from_attributes": True
    }

class OrderAssignmentCreate(BaseModel):
    user_id: int
    role: StaffRole

class UpdateOrderItemStatus(BaseModel):
    status: OrderItemStatus

class AssignedStaffWithOrder(BaseModel):
    order_id: int
    user_id: int
    role: StaffRole

    model_config = {
        "from_attributes": True
    }