from typing import List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models.orders import Order
from app.models.order_items import OrderItem
from app.models.menu_items import MenuItem
from app.models.order_assignments import OrderAssignment, StaffRole
from app.schemas import order as schemas

#Получить все заказы
def get_all_orders(db: Session) -> List[Order]:
    return db.query(Order).options(joinedload(Order.items)).all()

#Получить заказ по id
def get_order_by_id(order_id: int, db: Session) -> Order:
    order = db.query(Order).options(joinedload(Order.items)).filter(
        Order.order_id == order_id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order

# Создание нового заказа
def create_order(order_data: schemas.OrderCreate, db: Session) -> Order:
    new_order = Order(
        user_id=order_data.user_id if order_data.user_id else None,
        table_number=order_data.table_number,
        total_price=0,
        comment=order_data.comment
    )
    db.add(new_order)
    db.flush()

    for item in order_data.items:
        db_item = db.query(MenuItem).filter(MenuItem.item_id == item.item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail=f"Позиция меню {item.item_id} не найдена")
        new_order.total_price += db_item.price * item.quantity
        db.add(OrderItem(order_id=new_order.order_id, item_id=item.item_id, quantity=item.quantity, price=item.price))

    db.commit()
    db.refresh(new_order)
    return new_order

#Изменение статуса заказа
def update_order_status(order_id: int, status: schemas.OrderStatus, db: Session) -> Order:
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    order.status = status
    db.commit()
    db.refresh(order)
    return order

#Удаление заказа
def delete_order(order_id: int, db: Session):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
    db.query(OrderAssignment).filter(OrderAssignment.order_id == order_id).delete()
    db.delete(order)
    db.commit()
    return {"detail": "Заказ удалён"}

#Получение заказов конкретного пользователя
def get_orders_by_user(user_id: int, db: Session) -> List[Order]:
    return db.query(Order).filter(Order.user_id == user_id).all()

#Привязка персонала к заказу
def assign_staff_to_order(order_id: int, user_id: int, role: StaffRole, db: Session) -> Order:
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if role not in {"Waiter", "Barkeeper", "Cook"}:
        raise HTTPException(status_code=400, detail=f"Неверная роль: {role}")

    existing = db.query(OrderAssignment).filter(
        OrderAssignment.order_id == order_id,
        OrderAssignment.user_id == user_id,
        OrderAssignment.role == role
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже назначен на этот заказ с такой ролью")

    new_assignment = OrderAssignment(
        order_id=order_id,
        user_id=user_id,
        role=role
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    updated_order = db.query(Order).options(
        joinedload(Order.items)
    ).filter(Order.order_id == order_id).first()
    return updated_order

#получить весь персонал, привязанный к заказу
def get_all_assigned_staff_for_in_progress_orders(db: Session) -> List[OrderAssignment]:
    return (
        db.query(OrderAssignment)
        .join(Order, OrderAssignment.order_id == Order.order_id)
        .filter(Order.status == "In_progress")
        .all()
    )