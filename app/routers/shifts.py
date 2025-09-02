import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.staff_shifts import StaffShift
from app.database import get_db
from app.models.user import User
from app.schemas.shift import StaffShiftOut, StaffShiftCreate, StaffShiftUpdate
from app.services import shift_service
from app.realtime.websocket_manager import manager
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/shifts",
    tags=["Смены"]
)

#Получение смен
@router.get("/", response_model=List[StaffShiftOut])
async def get_all_shifts(db: Session = Depends(get_db), 
                         current_user: User = Depends(get_current_user)) -> List[StaffShift]:
    allowed_roles = {"Admin", "Barkeeper", "Cook", "Waiter"}
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    if current_user.role == "Admin":
        shifts = await asyncio.to_thread(shift_service.get_all_shifts, db)
    else:
        shifts = await asyncio.to_thread(shift_service.get_shifts_by_user, db, current_user.user_id)

    return shifts

#Получение смен конкретного пользователя
@router.get("/user/{user_id}", response_model=List[StaffShiftOut])
async def get_shifts_by_user(user_id: int, 
                             db: Session = Depends(get_db), 
                             current_user: User = Depends(get_current_user)) -> List[StaffShift]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return await asyncio.to_thread(shift_service.get_shifts_by_user, db, user_id)

#Создание смены
@router.post("/", response_model=StaffShiftOut)
async def create_shift(shift: StaffShiftCreate, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> StaffShift:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_shift = await asyncio.to_thread(shift_service.create_shift, db, shift)
    asyncio.create_task(manager.broadcast({
        "type": "shift_create",
        "payload": {"action": "create", "shift": StaffShiftOut.model_validate(new_shift).model_dump()}
    }))
    return new_shift

#Изменение смены
@router.put("/{shift_id}", response_model=StaffShiftOut)
async def update_shift(shift_id: int, 
                       shift: StaffShiftUpdate, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> StaffShift:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    updated_shift = await asyncio.to_thread(shift_service.update_shift, db, shift_id, shift)
    if not updated_shift:
        raise HTTPException(status_code=404, detail="Смена не найдена")
    asyncio.create_task(manager.broadcast({
        "type": "shift_update",
        "payload": {"action": "update", "shift": StaffShiftOut.model_validate(updated_shift).model_dump()}
    }))
    return updated_shift

#Удаление смены
@router.delete("/{shift_id}")
async def delete_shift(shift_id: int, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> dict[str, str]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    success = await asyncio.to_thread(shift_service.delete_shift, db, shift_id)
    if not success:
        raise HTTPException(status_code=404, detail="Смена не найдена")
    asyncio.create_task(manager.broadcast({
        "type": "shift_delete",
        "payload": {"action": "delete", "shift_id": shift_id}
    }))
    return {"detail": "Смена удалена"}