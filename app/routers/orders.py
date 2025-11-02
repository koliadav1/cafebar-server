import asyncio
from datetime import date
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.dependencies.cache import CacheManager, get_cache_manager
from app.models.order_items import OrderItem, OrderItemStatus
from app.models.orders import Order
from app.schemas import order as schema
from app.models.order_assignments import OrderAssignment, StaffRole
from app.services import order_service
from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User, UserRole
from app.realtime.websocket_manager import manager

router = APIRouter(prefix="/orders", tags=["Заказы"])

# Получить список заказов
@router.get("/", response_model=List[schema.OrderOut])
async def get_orders(db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    cache: CacheManager = Depends(get_cache_manager)) -> List[Order]:
    start_time = time.time()
    cache_key = f"orders:user:{current_user.user_id}:role:{current_user.role}"

    cached_orders = await cache.get_cached(cache_key)
    if cached_orders:
        print(f"[REDIS] Orders from cache - {time.time() - start_time:.3f}s")
        return cached_orders

    if current_user.role == "Client":
        orders = await order_service.get_orders_by_user(current_user.user_id, db)
    else:
        orders = await order_service.get_all_orders(db)
    db_time = time.time() - start_time
    print(f"[REDIS] Orders from database - {db_time:.3f}s")

    orders_out = [schema.OrderOut.model_validate(order) for order in orders]
    ttl = 15 if current_user.role == "Client" else 30
    await cache.set_cached(cache_key, [order.model_dump() for order in orders_out], ttl=ttl)

    return orders_out

# Получить все назначения персонала
@router.get("/assigned_staff", response_model=list[schema.AssignedStaffWithOrder])
async def get_all_assigned_staff_for_in_progress_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cache: CacheManager = Depends(get_cache_manager)) -> List[OrderAssignment]:
    allowed_roles = {"Admin", "Waiter", "Barkeeper", "Cook"}
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    start_time = time.time()
    cache_key = "orders:assigned_staff:in_progress"

    cached_assignments = await cache.get_cached(cache_key)
    if cached_assignments:
        print(f"[REDIS] Assigned staff from cache - {time.time() - start_time:.3f}s")
        return cached_assignments

    assignments = await order_service.get_all_assigned_staff_for_in_progress_orders(db)
    db_time = time.time() - start_time
    print(f"[REDIS] Assigned staff from database - {db_time:.3f}s")
    
    assignments_out = [schema.AssignedStaffWithOrder.model_validate(assignment) for assignment in assignments]

    await cache.set_cached(cache_key, [assignment.model_dump() for assignment in assignments_out], ttl=30)

    return assignments_out

# Получить заказ по id
@router.get("/{order_id}", response_model=schema.OrderOut)
async def get_order(order_id: int, 
                    db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    cache: CacheManager = Depends(get_cache_manager)) -> Order:
    if current_user.role not in ["Admin", "Barkeeper", "Cook", "Waiter"]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    start_time = time.time()
    cache_key = f"order:{order_id}"

    cached_order = await cache.get_cached(cache_key)
    if cached_order:
        print(f"[REDIS] Order from cache - {time.time() - start_time:.3f}s")
        return cached_order

    order = await order_service.get_order_by_id(order_id, db)
    db_time = time.time() - start_time
    print(f"[REDIS] Order from database - {db_time:.3f}s")
    
    order_out = schema.OrderOut.model_validate(order)
    
    await cache.set_cached(cache_key, order_out.model_dump(), ttl=60)
    
    return order_out

# Создать заказ
@router.post("/", response_model=schema.OrderOut)
async def create_order(order: schema.OrderCreate, 
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       cache: CacheManager = Depends(get_cache_manager)) -> Order:
    if current_user.role != "Client" and current_user.role != "Waiter":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_order = await order_service.create_order(order, db)

    await cache.invalidate_pattern("recommendations:popular:*")
    await cache.invalidate_pattern("recommendations:drinks:popular:*")
    await cache.invalidate_pattern("orders:user:*")
    await cache.invalidate_pattern("orders:assigned_staff:*")
    if current_user.role == UserRole.CLIENT:
        await cache.redis.delete(f"recommendations:personal:{current_user.user_id}:*")
        await cache.redis.delete(f"recommendations:drinks:personal:{current_user.user_id}:*")
        
    asyncio.create_task(manager.broadcast({
        "type": "order_create",
        "payload": {"action": "create", "order": schema.OrderOut.model_validate(new_order).model_dump()}
    }))
    return new_order

# Удаление заказа по id
@router.delete("/{order_id}")
async def delete_order(order_id: int, 
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)) -> dict[str, str]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    result = await order_service.delete_order(order_id, db)
    asyncio.create_task(manager.broadcast({
        "type": "order_delete",
        "payload": {"action": "delete", "order_id": order_id}
    }))
    return result

# Изменить статус заказа
@router.patch("/{order_id}/status", response_model=schema.OrderOut)
async def update_status(order_id: int, 
                        status: schema.OrderStatus = Query(...), 
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user),
                        cache: CacheManager = Depends(get_cache_manager)) -> Order:
    order = await order_service.get_order_by_id(order_id, db)
    if order.status in [schema.OrderStatus.COMPLETED, schema.OrderStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Нельзя менять статус у завершенных или отмененных заказов")
    if status == schema.OrderStatus.READY:
        raise HTTPException(status_code=400, detail="Заказ завершится сам")

    if current_user.role == "Client":
        if order.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Клиенты могут менять статус только у своих заказов")

        if status != schema.OrderStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Клиенты могут менять статус только на 'Отменен'")

        if order.status == schema.OrderStatus.READY:
            raise HTTPException(status_code=400, detail="Нельзя отменить готовый заказ")

    updated_order = await order_service.update_order_status(order_id, status, db)

    today = date.today().isoformat()
    await cache.redis.delete(f"order:{order_id}")
    await cache.invalidate_pattern("orders:user:*") 
    await cache.invalidate_pattern("orders:assigned_staff:*")
    await cache.invalidate_pattern(f"statistics:staff:*:start:{today}*")
    await cache.invalidate_pattern(f"statistics:staff:*admin:True*")
    
    asyncio.create_task(manager.broadcast({
        "type": "order_update",
        "payload": {"action": "update", "order": schema.OrderOut.model_validate(updated_order).model_dump()}
    }))
    return updated_order

# Назначить исполнителя к заказу
@router.patch("/{order_id}/assign", response_model=schema.OrderOut)
async def assign_self_to_order(order_id: int, 
                               db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user),
                               cache: CacheManager = Depends(get_cache_manager)) -> Order:
    try:
        staff_role = StaffRole(current_user.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверная роль")

    updated_order = await order_service.assign_staff_to_order(
        order_id,
        current_user.user_id,
        staff_role,
        db
    )

    asyncio.create_task(manager.broadcast({
        "type": "order_update",
        "payload": {"action": "update", "order": schema.OrderOut.model_validate(updated_order).model_dump()}
    }))

    await cache.redis.delete(f"order:{order_id}")
    await cache.invalidate_pattern("orders:assigned_staff:*")

    return updated_order

# Изменить статус позиции заказа
@router.patch("/order-items/{order_item_id}/status")
async def update_order_item_status(order_item_id: int,
                                   update_data: schema.UpdateOrderItemStatus,
                                   db: AsyncSession = Depends(get_db),
                                   current_user: User = Depends(get_current_user),
                                   cache: CacheManager = Depends(get_cache_manager)) -> dict[str, str]:
    allowed_roles = ["Cook", "Barkeeper", "Waiter"]
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    if current_user.role in ["Cook", "Barkeeper"] and update_data.status == OrderItemStatus.COMPLETED:
        raise HTTPException(status_code=403, detail="Вы не можете установить статус 'Завершено'")

    if current_user.role == "Waiter" and update_data.status != OrderItemStatus.COMPLETED:
        raise HTTPException(status_code=403, detail="Вы можете поменять статус только на 'Завершено'")

    result = await db.execute(select(OrderItem).where(OrderItem.order_item_id == order_item_id))
    order_item = result.scalar_one_or_none()
    if not order_item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    order_item.status = update_data.status
    await db.commit()
    await db.refresh(order_item)

    order_result = await db.execute(select(Order).where(Order.order_id == order_item.order_id))
    order = order_result.scalar_one_or_none()
    
    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order_item.order_id))
    order_items = items_result.scalars().all()

    if order and all(item.status == OrderItemStatus.READY for item in order_items):
        order.status = schema.OrderStatus.READY
        await db.commit()
        await db.refresh(order)

        asyncio.create_task(manager.broadcast({
            "type": "order_update",
            "payload": {"action": "update", "order": schema.OrderOut.model_validate(order).model_dump()}
        }))
        
    if order and all(item.status == OrderItemStatus.COMPLETED for item in order_items):
        order.status = schema.OrderStatus.COMPLETED
        await db.commit()
        await db.refresh(order)

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

    await cache.redis.delete(f"order:{order_item.order_id}")
    await cache.invalidate_pattern("orders:assigned_staff:*")

    return {"detail": "Статус позиции заказа обновлен"}