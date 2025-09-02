from pydantic import BaseModel
from typing import Optional

from app.models.resume import ResumeStatus

class ResumeBase(BaseModel):
    content: str
    phone_number: str

class ResumeCreate(ResumeBase):
    pass

class ResumeUpdateResponse(BaseModel):
    response: str

class ResumeUpdateStatus(BaseModel):
    status: ResumeStatus

class ResumeOut(ResumeBase):
    resume_id: int
    response: Optional[str]
    status: ResumeStatus

    model_config = {
        "from_attributes": True
    }
