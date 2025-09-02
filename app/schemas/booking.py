from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from app.models.table_booking import BookingStatus


class TableBookingBase(BaseModel):
    table_number: int = Field(..., gt=0)
    booking_time: datetime
    customer_name: str
    phone_number: str
    user_id: Optional[int] = None
    status: BookingStatus = BookingStatus.CONFIRMED
    duration_minutes: int = Field(default=120, gt=0)

class TableBookingCreate(TableBookingBase):
    pass

class TableBookingUpdate(BaseModel):
    table_number: Optional[int] = Field(None, gt=0)
    booking_time: Optional[datetime] = None
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[BookingStatus] = None
    duration_minutes: Optional[int] = Field(None, gt=0)

class TableBookingResponse(TableBookingBase):
    booking_id: int

    model_config = {
        "from_attributes": True
    }