import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.supply_orders import SupplyOrder, SupplyStatus
from app.models.user import User
from app.schemas.supply import SupplyOrderCreate, SupplyOrderOut, SupplyOrderUpdate
from app.services import supply_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/supply-orders", tags=["Поставки"])

#Создание поставки
@router.post("/", response_model=SupplyOrderOut)
async def create_order(order_data: SupplyOrderCreate, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> SupplyOrder:
    return await asyncio.to_thread(supply_service.create_supply_order, db, order_data)

#Получение поставок
@router.get("/", response_model=List[SupplyOrderOut])
async def get_all_orders(db: Session = Depends(get_db), 
                         current_user: User = Depends(get_current_user)) -> List[SupplyOrder]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return await asyncio.to_thread(supply_service.get_all_orders, db)

#Получение просроченых поставок
@router.get("/overdue", response_model=List[SupplyOrderOut])
async def get_overdue_orders(db: Session = Depends(get_db), 
                             current_user: User = Depends(get_current_user)) -> List[SupplyOrder]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return await asyncio.to_thread(supply_service.get_overdue_orders, db)

#Получение поставки по id
@router.get("/{order_id}", response_model=SupplyOrderOut)
async def get_order(order_id: int, 
                    db: Session = Depends(get_db), 
                    current_user: User = Depends(get_current_user)) -> SupplyOrder:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    order = await asyncio.to_thread(supply_service.get_order_by_id, db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Поставка не найдена")
    return order

#Изменение поставки
@router.put("/{order_id}", response_model=SupplyOrderOut)
async def update_order(order_id: int, 
                       updates: SupplyOrderUpdate, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> SupplyOrder:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    updated = await asyncio.to_thread(supply_service.update_order, db, order_id, updates)
    db_order = await asyncio.to_thread(supply_service.get_order_by_id, db, order_id)

    if not updated:
        if not db_order:
            raise HTTPException(status_code=404, detail="Поставка не найдена")
        if db_order.status == SupplyStatus.CANCELLED and updates.delivery_date:
            raise HTTPException(status_code=403, detail="Нельзя менять дату доставки для отмененных поставок")
        raise HTTPException(status_code=400, detail="Изменения не применены")

    return updated

#Удаление поставки
@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: int, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    success = await asyncio.to_thread(supply_service.delete_order, db, order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Поставка не найдена")