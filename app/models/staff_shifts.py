from sqlalchemy import Column, Integer, Date, Time, ForeignKey, CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_method

from app.database import Base

class StaffShift(Base):
    __tablename__ = "staff_shifts"
    __table_args__ = (
        CheckConstraint('shift_end > shift_start', name='check_shift_end_after_start'),
    )

    shift_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    shift_date = Column(Date, nullable=False)
    shift_start = Column(Time, nullable=False)
    shift_end = Column(Time, nullable=False)

    @hybrid_method
    def duration(self):
        return (self.shift_end - self.shift_start)