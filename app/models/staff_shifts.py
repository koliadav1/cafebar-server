from datetime import datetime
from sqlalchemy import Column, Integer, Date, Time, ForeignKey, CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

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
    
    @hybrid_property
    def is_active(self):
        now = datetime.now()
        today = now.date()
        current_time = now.time()
        
        return (self.shift_date == today and 
                self.shift_start <= current_time <= self.shift_end)
    
    @hybrid_property
    def is_future(self):
        now = datetime.now()
        return (self.shift_date > now.date() or 
                (self.shift_date == now.date() and self.shift_start > now.time()))
    
    @hybrid_property  
    def is_past(self):
        now = datetime.now()
        return (self.shift_date < now.date() or
                (self.shift_date == now.date() and self.shift_end < now.time()))