from pydantic import BaseModel, Field
from datetime import date, time

class StaffShiftBase(BaseModel):
    user_id: int = Field(..., ge=1)
    shift_date: date
    shift_start: time
    shift_end: time

class StaffShiftCreate(StaffShiftBase):
    pass

class StaffShiftUpdate(StaffShiftBase):
    pass

class StaffShiftOut(StaffShiftBase):
    shift_id: int

    model_config = {
        "from_attributes": True
    }