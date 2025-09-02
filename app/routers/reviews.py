import asyncio

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.review import AdminReviewResponse, ReviewCreate, ReviewUpdate, Review
from app.services.auth_service import get_current_user
from app.services import review_service as service

router = APIRouter(prefix="/reviews", tags=["Отзывы"])

#ПОлучение отзывов
@router.get("/", response_model=list[Review])
async def get_all_reviews(db: Session = Depends(get_db), 
                          current_user: User = Depends(get_current_user)) -> List[Review]:
    if current_user.role == "Admin":
        # Админ видит все отзывы
        return await asyncio.to_thread(service.get_all_reviews, db=db)
    elif current_user.role == "Client":
        # Клиент видит только свои отзывы
        return await asyncio.to_thread(service.get_reviews_by_user, db=db, user_id=current_user.user_id)
    else:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

#Создание отзыва
@router.post("/", response_model=Review)
async def create_review(review_data: ReviewCreate, 
                        db: Session = Depends(get_db), 
                        current_user: User = Depends(get_current_user)) -> Review:
    if current_user.role != "Client":
        raise HTTPException(status_code=403, detail="Только клиенты могут оставлять отзывы")
    return await asyncio.to_thread(service.create_review, db, review_data, current_user.user_id)

#Получение отзывов пользователя по его id
@router.get("/user/{user_id}", response_model=list[Review])
async def get_reviews_by_user(user_id: int, 
                              db: Session = Depends(get_db), 
                              current_user: User = Depends(get_current_user)) -> List[Review]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return await asyncio.to_thread(service.get_reviews_by_user, db=db, user_id=user_id)

#Получение отзыва по id
@router.get("/{review_id}", response_model=Review)
async def get_review(review_id: int, db: Session = Depends(get_db)) -> Review:
    db_review = await asyncio.to_thread(service.get_review_by_id, db=db, review_id=review_id)
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return db_review

#Изменение отзыва
@router.put("/{review_id}", response_model=Review)
async def update_review(review_id: int, 
                        review_update: ReviewUpdate, 
                        db: Session = Depends(get_db), 
                        current_user: User = Depends(get_current_user)) -> Review:
    if current_user.role != "Client":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    existing_review = await asyncio.to_thread(service.get_review_by_id, db=db, review_id=review_id)
    if not existing_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    if existing_review.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Изменять можно только свои отзывы")
    
    db_review = await asyncio.to_thread(service.update_review, db=db, review_id=review_id, review_update=review_update)
    if not db_review:
        raise HTTPException(status_code=400, detail="Изменения не применены")
    return db_review

#Удаление отзыва
@router.delete("/{review_id}", response_model=Review)
async def delete_review(review_id: int, 
                        db: Session = Depends(get_db), 
                        current_user: User = Depends(get_current_user)) -> Review:
    if current_user.role == "Admin":
        db_review = await asyncio.to_thread(service.delete_review, db=db, review_id=review_id)
        if not db_review:
            raise HTTPException(status_code=404, detail="Отзыв не найден")
        return db_review

    elif current_user.role == "Client":
        existing_review = await asyncio.to_thread(service.get_review_by_id, db=db, review_id=review_id)
        if not existing_review:
            raise HTTPException(status_code=404, detail="Отзыв не найден")
        if existing_review.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Вы можете удалить только свой отзыв")

        db_review = await asyncio.to_thread(service.delete_review, db=db, review_id=review_id)
        return db_review

    else:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

#Ответ на отзыв
@router.post("/{review_id}/response", response_model=Review)
async def respond_to_review(review_id: int, 
                            response_data: AdminReviewResponse, 
                            db: Session = Depends(get_db), 
                            current_user: User = Depends(get_current_user)) -> Review:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут отвечать на отзывы")
    try:
        return await asyncio.to_thread(service.respond_to_review, db=db, review_id=review_id, response=response_data.admin_response)
    except ValueError:
        raise HTTPException(status_code=404, detail="Отзыв не найден")