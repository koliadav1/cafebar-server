from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.orders import Order
from app.models.order_items import OrderItem
from app.models.menu_items import MenuItem, MenuCategory
from app.schemas.recommendation import RecommendedItem

#Получение самых популярных блюд
def get_most_popular_items(db: Session, limit: int = 5) -> list[RecommendedItem]:
    results = (
        db.query(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(MenuItem.category != MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
        .all()
    )
    return [RecommendedItem.model_validate(row) for row in results]

#Получить самые популярные блюда конкретного пользователя
def get_user_recommendations(user_id: int, db: Session, limit: int = 5) -> list[RecommendedItem]:
    results = (
        db.query(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(Order.user_id == user_id, MenuItem.category != MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
        .all()
    )
    return [RecommendedItem.model_validate(row) for row in results]

#Получить самые популярные напитки
def get_most_popular_drinks(db: Session, limit: int = 5) -> list[RecommendedItem]:
    results = (
        db.query(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(MenuItem.category == MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
        .all()
    )
    return [RecommendedItem.model_validate(row) for row in results]

#Получить самые популярные напитки конкретного пользователя
def get_user_drink_recommendations(user_id: int, db: Session, limit: int = 5) -> list[RecommendedItem]:
    results = (
        db.query(
            MenuItem.item_id,
            MenuItem.name,
            MenuItem.category,
            func.count(OrderItem.order_item_id).label("order_count")
        )
        .join(OrderItem, MenuItem.item_id == OrderItem.item_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(Order.user_id == user_id, MenuItem.category == MenuCategory.DRINK)
        .group_by(MenuItem.item_id)
        .order_by(func.count(OrderItem.order_item_id).desc())
        .limit(limit)
        .all()
    )
    return [RecommendedItem.model_validate(row) for row in results]
