from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.orders import Order
from app.models.order_items import OrderItem
from app.models.menu_items import MenuItem, MenuCategory
from app.schemas.recommendation import RecommendedItem

# Получение самых популярных блюд
async def get_most_popular_items(db: AsyncSession, limit: int = 5) -> list[RecommendedItem]:
    stmt = (
        select(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .where(MenuItem.category != MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    return [RecommendedItem.model_validate(row) for row in rows]

# Получить самые популярные блюда конкретного пользователя
async def get_user_recommendations(user_id: int, db: AsyncSession, limit: int = 5) -> list[RecommendedItem]:
    stmt = (
        select(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .where(Order.user_id == user_id, MenuItem.category != MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    return [RecommendedItem.model_validate(row) for row in rows]

# Получить самые популярные напитки
async def get_most_popular_drinks(db: AsyncSession, limit: int = 5) -> list[RecommendedItem]:
    stmt = (
        select(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .where(MenuItem.category == MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    return [RecommendedItem.model_validate(row) for row in rows]

# Получить самые популярные напитки конкретного пользователя
async def get_user_drink_recommendations(user_id: int, db: AsyncSession, limit: int = 5) -> list[RecommendedItem]:
    stmt = (
        select(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .where(Order.user_id == user_id, MenuItem.category == MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    return [RecommendedItem.model_validate(row) for row in rows]