from sqlalchemy import Column, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from enum import Enum

from app.database import Base

class ResumeStatus(str, Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"

class Resume(Base):
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    phone_number = Column(String, nullable=False)
    response = Column(Text, nullable=True)
    status = Column(SQLEnum(ResumeStatus), nullable=False, default=ResumeStatus.PENDING)
