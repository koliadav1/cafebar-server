from pydantic import BaseModel, Field
from enum import Enum

from app.models.order_assignments import StaffRole

class StaffStatsOut(BaseModel):
    user_id: int = Field(..., ge=1)
    role: StaffRole
    orders_count: int

    model_config = {
        "from_attributes": True
    }
    
class StaffStatsWithRankOut(BaseModel):
    user_id: int
    role: StaffRole
    orders_count: int
    rating: int | None
    total_employees: int | None

    model_config = {
        "from_attributes": True
    }