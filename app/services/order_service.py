from datetime import date, datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.orders import Order
from app.models.order_items import OrderItem
from app.models.menu_items import MenuItem
from app.models.order_assignments import OrderAssignment, StaffRole
from app.models.staff_shifts import StaffShift
from app.models.user import User
from app.schemas import order as schemas
from app.services.shift_service import get_user_active_shift

# Получить все заказы
async def get_all_orders(db: AsyncSession) -> List[Order]:
    result = await db.execute(
        select(Order).options(selectinload(Order.items))
    )
    return result.scalars().all()

# Получить заказ по id
async def get_order_by_id(order_id: int, db: AsyncSession) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.order_id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.assignments)
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order

# Создание нового заказа
async def create_order(order_data: schemas.OrderCreate, db: AsyncSession) -> Order:
    new_order = Order(
        user_id=order_data.user_id if order_data.user_id else None,
        table_number=order_data.table_number,
        total_price=0,
        comment=order_data.comment
    )
    db.add(new_order)
    await db.flush()

    for item in order_data.items:
        result = await db.execute(select(MenuItem).where(MenuItem.item_id == item.item_id))
        db_item = result.scalar_one_or_none()
        if not db_item:
            raise HTTPException(status_code=404, detail=f"Позиция меню {item.item_id} не найдена")
        new_order.total_price += db_item.price * item.quantity
        db.add(OrderItem(order_id=new_order.order_id, item_id=item.item_id, quantity=item.quantity, price=item.price))

    await db.commit()
    await db.refresh(new_order)
    return new_order

# Изменение статуса заказа
async def update_order_status(order_id: int, status: schemas.OrderStatus, db: AsyncSession) -> Order:
    result = await db.execute(select(Order).where(Order.order_id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    order.status = status
    await db.commit()
    await db.refresh(order)
    return order

# Удаление заказа
async def delete_order(order_id: int, db: AsyncSession):
    result = await db.execute(select(Order).where(Order.order_id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    await db.execute(delete(OrderItem).where(OrderItem.order_id == order_id))
    await db.execute(delete(OrderAssignment).where(OrderAssignment.order_id == order_id))
    await db.delete(order)
    await db.commit()
    return {"detail": "Заказ удалён"}

# Получение заказов конкретного пользователя
async def get_orders_by_user(user_id: int, db: AsyncSession) -> List[Order]:
    result = await db.execute(select(Order).where(Order.user_id == user_id))
    return result.scalars().all()

# Привязка персонала к заказу
async def assign_staff_to_order(order_id: int, user_id: int, role: StaffRole, db: AsyncSession) -> Order:
    result = await db.execute(select(Order).where(Order.order_id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if role not in {"Waiter", "Barkeeper", "Cook"}:
        raise HTTPException(status_code=400, detail=f"Неверная роль: {role}")
    
    active_shift = await get_user_active_shift(db, user_id)
    
    if not active_shift:
        raise HTTPException(
            status_code=400, 
            detail="Сотрудник не в активной смене. Невозможно назначить на заказ."
        )
    
    existing_result = await db.execute(
        select(OrderAssignment).where(
            OrderAssignment.order_id == order_id,
            OrderAssignment.user_id == user_id,
            OrderAssignment.role == role
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже назначен на этот заказ с такой ролью")

    new_assignment = OrderAssignment(
        order_id=order_id,
        user_id=user_id,
        role=role
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)

    updated_result = await db.execute(
        select(Order)
        .where(Order.order_id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.assignments)
        )
    )
    updated_order = updated_result.scalar_one_or_none()
    return updated_order

# получить весь персонал, привязанный к заказу
async def get_all_assigned_staff_for_in_progress_orders(db: AsyncSession) -> List[OrderAssignment]:
    result = await db.execute(
        select(OrderAssignment)
        .join(Order, OrderAssignment.order_id == Order.order_id)
        .where(Order.status == "In_progress")
    )
    return result.scalars().all()