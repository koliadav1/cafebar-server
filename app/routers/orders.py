import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.models.order_items import OrderItem, OrderItemStatus
from app.models.orders import Order
from app.schemas import order as schema
from app.models.order_assignments import OrderAssignment, StaffRole
from app.services import order_service
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.realtime.websocket_manager import manager

router = APIRouter(prefix="/orders", tags=["Заказы"])

# Получить список заказов
@router.get("/", response_model=List[schema.OrderOut])
async def get_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> List[Order]:
    if current_user.role == "Client":
        orders = await asyncio.to_thread(order_service.get_orders_by_user, current_user.user_id, db)
    else:
        orders = await asyncio.to_thread(order_service.get_all_orders, db)
    return orders

#Получить все назначения персонала
@router.get("/assigned_staff", response_model=list[schema.AssignedStaffWithOrder])
def get_all_assigned_staff_for_in_progress_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)) -> List[OrderAssignment]:
    allowed_roles = {"Admin", "Waiter", "Barkeeper", "Cook"}
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    assignments = order_service.get_all_assigned_staff_for_in_progress_orders(db)
    return assignments

# Получить заказ по id
@router.get("/{order_id}", response_model=schema.OrderOut)
async def get_order(order_id: int, 
                    db: Session = Depends(get_db), 
                    current_user: User = Depends(get_current_user)) -> Order:
    if current_user.role not in ["Admin", "Barkeeper", "Cook", "Waiter"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    order = await asyncio.to_thread(order_service.get_order_by_id, order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order

# Создать заказ
@router.post("/", response_model=schema.OrderOut)
async def create_order(order: schema.OrderCreate, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> Order:
    if current_user.role != "Client" and current_user.role != "Waiter":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_order = await asyncio.to_thread(order_service.create_order, order, db)
    asyncio.create_task(manager.broadcast({
        "type": "order_create",
        "payload": {"action": "create", "order": schema.OrderOut.model_validate(new_order).model_dump()}
    }))
    return new_order

#Удаление заказа по id
@router.delete("/{order_id}")
async def delete_order(order_id: int, 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(get_current_user)) -> dict[str, str]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    result = await asyncio.to_thread(order_service.delete_order, order_id, db)
    asyncio.create_task(manager.broadcast({
        "type": "order_delete",
        "payload": {"action": "delete", "order_id": order_id}
    }))
    return result

# Изменить статус заказа
@router.patch("/{order_id}/status", response_model=schema.OrderOut)
async def update_status(order_id: int, 
                        status: schema.OrderStatus = Query(...), 
                        db: Session = Depends(get_db), 
                        current_user: User = Depends(get_current_user)) -> Order:
    order = await asyncio.to_thread(order_service.get_order_by_id, order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status in [schema.OrderStatus.COMPLETED, schema.OrderStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Нельзя менять статус у завершенных или отмененных заказов")
    if status == schema.OrderStatus.READY:
        raise HTTPException(status_code=400, detail="Заказ завершится сам") #После выдачи всех позиций заказа

    if current_user.role == "Client":
        if order.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Клиенты могут менять статус только у своих заказов")

        if status != schema.OrderStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Клиенты могут менять статус только на 'Отменен'")

        if order.status == schema.OrderStatus.READY:
            raise HTTPException(status_code=400, detail="Нельзя отменить готовый заказ")

    updated_order = await asyncio.to_thread(order_service.update_order_status, order_id, status, db)
    asyncio.create_task(manager.broadcast({
        "type": "order_update",
        "payload": {"action": "update", "order": schema.OrderOut.model_validate(updated_order).model_dump()}
    }))
    return updated_order

# Назначить исполнителя к заказу
@router.patch("/{order_id}/assign", response_model=schema.OrderOut)
async def assign_self_to_order(order_id: int, 
                               db: Session = Depends(get_db), 
                               current_user: User = Depends(get_current_user)) -> Order:
    order = await asyncio.to_thread(order_service.get_order_by_id, order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if current_user.role not in ["Cook", "Barkeeper", "Waiter"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        staff_role = StaffRole(current_user.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверная роль")

    updated_order = await asyncio.to_thread(
        order_service.assign_staff_to_order,
        order_id,
        current_user.user_id,
        staff_role,
        db
    )

    asyncio.create_task(manager.broadcast({
        "type": "order_update",
        "payload": {"action": "update", "order": schema.OrderOut.model_validate(updated_order).model_dump()}
    }))

    return updated_order

#Изменить статус позиции заказа
@router.patch("/order-items/{order_item_id}/status")
async def update_order_item_status(
    order_item_id: int,
    update_data: schema.UpdateOrderItemStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)) -> dict[str, str]:
    allowed_roles = ["Cook", "Barkeeper", "Waiter"]
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    if current_user.role in ["Cook", "Barkeeper"] and update_data.status == OrderItemStatus.COMPLETED:
        raise HTTPException(status_code=403, detail="Вы не можете установить статус 'Завершено'")

    if current_user.role == "Waiter" and update_data.status != OrderItemStatus.COMPLETED:
        raise HTTPException(status_code=403, detail="Вы можете поменять статус только на 'Завершено'")

    order_item = db.query(OrderItem).filter(OrderItem.order_item_id == order_item_id).first()
    if not order_item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    order_item.status = update_data.status
    db.commit()
    db.refresh(order_item)

    order = db.query(Order).filter(Order.order_id == order_item.order_id).first()
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_item.order_id).all()

    if order and all(item.status == OrderItemStatus.READY for item in order_items):
        order.status = schema.OrderStatus.READY
        db.commit()
        db.refresh(order)

        asyncio.create_task(manager.broadcast({
            "type": "order_update",
            "payload": {"action": "update", "order": schema.OrderOut.model_validate(order).model_dump()}
        }))
        
    if order and all(item.status == OrderItemStatus.COMPLETED for item in order_items):
        order.status = schema.OrderStatus.COMPLETED
        db.commit()
        db.refresh(order)    

        asyncio.create_task(manager.broadcast({
            "type": "order_update",
            "payload": {"action": "update", "order": schema.OrderOut.model_validate(order).model_dump()}
        }))

    asyncio.create_task(manager.broadcast({
        "type": "order_item_update",
        "payload": {
            "action": "update",
            "order_id": order_item.order_id,
            "order_item_id": order_item.order_item_id,
            "item_status": order_item.status
        }
    }))

    return {"detail": "Статус позиции заказа обнослен"}