from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.orders import Order
from app.models.reviews import Review
from app.schemas.review import ReviewCreate, ReviewUpdate

# Получить все отзывы
async def get_all_reviews(db: AsyncSession) -> List[Review]:
    result = await db.execute(select(Review))
    return result.scalars().all()

# Создать отзыв
async def create_review(db: AsyncSession, review_data: ReviewCreate, user_id: int) -> Review:
    result = await db.execute(
        select(Order).where(
            Order.order_id == review_data.order_id, 
            Order.user_id == user_id
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=403, detail="Вы можете оставлять отзывы только к своим заказам")

    db_review = Review(
        user_id=user_id,
        order_id=review_data.order_id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review

# Получить отзывы конкретного пользователя
async def get_reviews_by_user(db: AsyncSession, user_id: int) -> List[Review]:
    result = await db.execute(select(Review).where(Review.user_id == user_id))
    return result.scalars().all()

# Получить отзыв по id
async def get_review_by_id(db: AsyncSession, review_id: int) -> Review:
    result = await db.execute(select(Review).where(Review.review_id == review_id))
    return result.scalar_one_or_none()

# Изменить отзыв
async def update_review(db: AsyncSession, review_id: int, review_update: ReviewUpdate) -> Review:
    result = await db.execute(select(Review).where(Review.review_id == review_id))
    db_review = result.scalar_one_or_none()
    if db_review:
        db_review.rating = review_update.rating
        db_review.comment = review_update.comment
        await db.commit()
        await db.refresh(db_review)
    return db_review

# Удалить отзыв
async def delete_review(db: AsyncSession, review_id: int) -> Review:
    result = await db.execute(select(Review).where(Review.review_id == review_id))
    db_review = result.scalar_one_or_none()
    if db_review:
        await db.delete(db_review)
        await db.commit()
    return db_review

# Ответить на отзыв
async def respond_to_review(db: AsyncSession, review_id: int, response: str) -> Review:
    result = await db.execute(select(Review).where(Review.review_id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise ValueError("Отзыв не найден")

    review.admin_response = response
    await db.commit()
    await db.refresh(review)
    return review