from enum import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, Integer, String, TIMESTAMP

from app.database import Base

class UserRole(str, Enum):
    ADMIN = 'Admin'
    WAITER = 'Waiter'
    COOK = 'Cook'
    BARKEEPER = 'Barkeeper'
    CLIENT = 'Client'

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String)
    phone_number = Column(String)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CLIENT)
    created_at = Column(TIMESTAMP)