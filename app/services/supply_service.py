from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.supply_orders import SupplyOrder, SupplyStatus
from app.schemas.supply import SupplyOrderCreate, SupplyOrderUpdate

#Создать поставку
def create_supply_order(db: Session, order_data: SupplyOrderCreate) -> SupplyOrder:
    db_order = SupplyOrder(**order_data.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

#Получить все поставки
def get_all_orders(db: Session) -> List[SupplyOrder]:
    return db.query(SupplyOrder).all()

#Получить поставку по id
def get_order_by_id(db: Session, order_id: int) -> Optional[SupplyOrder]:
    return db.query(SupplyOrder).filter(SupplyOrder.supply_order_id == order_id).first()

#Изменить поставку
def update_order(db: Session, order_id: int, updates: SupplyOrderUpdate) -> Optional[SupplyOrder]:
    db_order = get_order_by_id(db, order_id)
    if db_order.status == SupplyStatus.CANCELLED and updates.delivery_date:
        return 0
    if not db_order:
        return None
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order

#Удалить поставку
def delete_order(db: Session, order_id: int) -> bool:
    db_order = get_order_by_id(db, order_id)
    if not db_order:
        return False
    db.delete(db_order)
    db.commit()
    return True

#Получить задерживающиеся поставки
def get_overdue_orders(db: Session) -> List[SupplyOrder]:
    now = datetime.now()
    return db.query(SupplyOrder).filter(
        SupplyOrder.status == 'Pending',
        SupplyOrder.delivery_date != None,
        SupplyOrder.delivery_date < now
    ).all()
