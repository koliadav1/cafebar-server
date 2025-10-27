from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.models.supply_orders import SupplyOrder, SupplyStatus
from app.schemas.supply import SupplyOrderCreate, SupplyOrderUpdate

# Создать поставку
async def create_supply_order(db: AsyncSession, order_data: SupplyOrderCreate) -> SupplyOrder:
    db_order = SupplyOrder(**order_data.model_dump())
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order

# Получить все поставки
async def get_all_orders(db: AsyncSession) -> List[SupplyOrder]:
    result = await db.execute(select(SupplyOrder))
    return result.scalars().all()

# Получить поставку по id
async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[SupplyOrder]:
    result = await db.execute(
        select(SupplyOrder).where(SupplyOrder.supply_order_id == order_id)
    )
    return result.scalar_one_or_none()

# Изменить поставку
async def update_order(db: AsyncSession, order_id: int, updates: SupplyOrderUpdate) -> Optional[SupplyOrder]:
    db_order = await get_order_by_id(db, order_id)
    if not db_order:
        return None

    if db_order.status == SupplyStatus.CANCELLED and updates.delivery_date:
        return None
    
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_order, key, value)
    
    await db.commit()
    await db.refresh(db_order)
    return db_order

# Удалить поставку
async def delete_order(db: AsyncSession, order_id: int) -> bool:
    db_order = await get_order_by_id(db, order_id)
    if not db_order:
        return False
    await db.delete(db_order)
    await db.commit()
    return True

# Получить задерживающиеся поставки
async def get_overdue_orders(db: AsyncSession) -> List[SupplyOrder]:
    now = datetime.now()
    result = await db.execute(
        select(SupplyOrder).where(
            SupplyOrder.status == 'Pending',
            SupplyOrder.delivery_date != None,
            SupplyOrder.delivery_date < now
        )
    )
    return result.scalars().all()