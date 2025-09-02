from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.orders import Order
from app.models.reviews import Review
from app.schemas.review import ReviewCreate, ReviewUpdate

#Получить все отзывы
def get_all_reviews(db: Session) -> List[Review]:
    reviews = db.query(Review).all()
    return reviews

#Создать отзыв
def create_review(db: Session, review_data: ReviewCreate, user_id: int) -> Review:
    order = db.query(Order).filter_by(order_id=review_data.order_id, user_id=user_id).first()
    if not order:
        raise HTTPException(status_code=403, detail="Вы можете оставлять отзывы только к своим заказам")

    db_review = Review(
        user_id=user_id,
        order_id=review_data.order_id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

#Получить отзывы конкретного пользователя
def get_reviews_by_user(db: Session, user_id: int) -> List[Review]:
    return db.query(Review).filter(Review.user_id == user_id).all()

#Получить отзыв по id
def get_review_by_id(db: Session, review_id: int) -> Review:
    return db.query(Review).filter(Review.review_id == review_id).first()

#Изменить отзыв
def update_review(db: Session, review_id: int, review_update: ReviewUpdate) -> Review:
    db_review = db.query(Review).filter(Review.review_id == review_id).first()
    if db_review:
        db_review.rating = review_update.rating
        db_review.comment = review_update.comment
        db.commit()
        db.refresh(db_review)
    return db_review

#Удалить отзыв
def delete_review(db: Session, review_id: int) -> Review:
    db_review = db.query(Review).filter(Review.review_id == review_id).first()
    if db_review:
        db.delete(db_review)
        db.commit()
    return db_review

#Ответить на отзыв
def respond_to_review(db: Session, review_id: int, response: str) -> Review:
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review:
        raise ValueError("Отзыв не найден")

    review.admin_response = response
    db.commit()
    db.refresh(review)
    return review