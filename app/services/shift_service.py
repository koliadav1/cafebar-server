from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.staff_shifts import StaffShift
from app.schemas.shift import StaffShiftCreate, StaffShiftUpdate

#Получить все смены
def get_all_shifts(db: Session) -> List[StaffShift]:
    return db.query(StaffShift).all()

#Получить смены конкретного пользователя
def get_shifts_by_user(db: Session, user_id: int) -> List[StaffShift]:
    return db.query(StaffShift).filter(StaffShift.user_id == user_id).all()

#Создать смену
def create_shift(db: Session, shift: StaffShiftCreate) -> StaffShift:
    db_shift = StaffShift(**shift.dict())
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift

#Изменить смену
def update_shift(db: Session, shift_id: int, shift_data: StaffShiftUpdate) -> Optional[StaffShift]:
    db_shift = db.query(StaffShift).filter(StaffShift.shift_id == shift_id).first()
    if not db_shift:
        return None
    for key, value in shift_data.dict().items():
        setattr(db_shift, key, value)
    db.commit()
    db.refresh(db_shift)
    return db_shift

#Удалить смену
def delete_shift(db: Session, shift_id: int) -> bool:
    db_shift = db.query(StaffShift).filter(StaffShift.shift_id == shift_id).first()
    if not db_shift:
        return False
    db.delete(db_shift)
    db.commit()
    return True
