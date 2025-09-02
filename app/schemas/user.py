from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.user import UserRole

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    password: str = Field(..., min_length=1)
    role: Optional[UserRole] = UserRole.CLIENT
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserOut(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: UserRole
    created_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)

class UserUpdate(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None