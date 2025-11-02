import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.cache import CacheManager, get_cache_manager
from app.models.user import User
from app.schemas.review import AdminReviewResponse, ReviewCreate, ReviewUpdate, Review
from app.services.auth_service import get_current_user
from app.services import review_service as service

router = APIRouter(prefix="/reviews", tags=["Отзывы"])

# Получение отзывов
@router.get("/", response_model=list[Review])
async def get_all_reviews(db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user),
                          cache: CacheManager = Depends(get_cache_manager)) -> List[Review]:
    start_time = time.time()
    if current_user.role == "Admin":
        cache_key = "reviews:all"
        
        cached_reviews = await cache.get_cached(cache_key)
        if cached_reviews:
            print(f"[REDIS] All reviews from cache - {time.time() - start_time:.3f}s")
            return cached_reviews

        reviews = await service.get_all_reviews(db=db)
        db_time = time.time() - start_time
        print(f"[REDIS] All reviews from database - {db_time:.3f}s")
        
        reviews_out = [Review.model_validate(review) for review in reviews]
        await cache.set_cached(cache_key, [review.model_dump() for review in reviews_out], ttl=3600)
        
        return reviews_out
    
    elif current_user.role == "Client":
        cache_key = f"reviews:user:{current_user.user_id}"
        
        cached_reviews = await cache.get_cached(cache_key)
        if cached_reviews:
            print(f"[REDIS] User reviews from cache - {time.time() - start_time:.3f}s")
            return cached_reviews

        reviews = await service.get_reviews_by_user(db=db, user_id=current_user.user_id)
        db_time = time.time() - start_time
        print(f"[REDIS] User reviews from database - {db_time:.3f}s")
        
        reviews_out = [Review.model_validate(review) for review in reviews]
        await cache.set_cached(cache_key, [review.model_dump() for review in reviews_out], ttl=1800)
        
        return reviews_out
    else:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

# Создание отзыва
@router.post("/", response_model=Review)
async def create_review(review_data: ReviewCreate, 
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user),
                        cache: CacheManager = Depends(get_cache_manager)) -> Review:
    if current_user.role != "Client":
        raise HTTPException(status_code=403, detail="Только клиенты могут оставлять отзывы")
    review = await service.create_review(db, review_data, current_user.user_id)
    review_out = Review.model_validate(review)
    
    await cache.invalidate_pattern("reviews:all")
    await cache.redis.delete(f"reviews:user:{current_user.user_id}")
    await cache.redis.delete(f"reviews:user:*")
    
    return review_out

# Получение отзывов пользователя по его id
@router.get("/user/{user_id}", response_model=list[Review])
async def get_reviews_by_user(user_id: int, 
                              db: AsyncSession = Depends(get_db),
                              current_user: User = Depends(get_current_user),
                              cache: CacheManager = Depends(get_cache_manager)) -> List[Review]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    start_time = time.time()
    cache_key = f"reviews:user:{user_id}"
    
    cached_reviews = await cache.get_cached(cache_key)
    if cached_reviews:
        print(f"[REDIS] User reviews by ID from cache - {time.time() - start_time:.3f}s")
        return cached_reviews

    reviews = await service.get_reviews_by_user(db=db, user_id=user_id)
    db_time = time.time() - start_time
    print(f"[REDIS] User reviews by ID from database - {db_time:.3f}s")
    
    reviews_out = [Review.model_validate(review) for review in reviews]
    await cache.set_cached(cache_key, [review.model_dump() for review in reviews_out], ttl=1800)
    
    return reviews_out

# Получение отзыва по id
@router.get("/{review_id}", response_model=Review)
async def get_review(review_id: int,
                     db: AsyncSession = Depends(get_db), 
                     cache: CacheManager = Depends(get_cache_manager)) -> Review:
    start_time = time.time()
    cache_key = f"review:{review_id}"

    cached_review = await cache.get_cached(cache_key)
    if cached_review:
        print(f"[REDIS] Review by ID from cache - {time.time() - start_time:.3f}s")
        return cached_review

    db_review = await service.get_review_by_id(db=db, review_id=review_id)
    db_time = time.time() - start_time
    print(f"[REDIS] Review by ID from database - {db_time:.3f}s")
    if not db_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    review_out = Review.model_validate(db_review)
    await cache.set_cached(cache_key, review_out.model_dump(), ttl=3600)
    
    return review_out

# Изменение отзыва
@router.put("/{review_id}", response_model=Review)
async def update_review(review_id: int, 
                        review_update: ReviewUpdate, 
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user),
                        cache: CacheManager = Depends(get_cache_manager)) -> Review:
    if current_user.role != "Client":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    existing_review = await service.get_review_by_id(db=db, review_id=review_id)
    if not existing_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    if existing_review.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Изменять можно только свои отзывы")
    
    db_review = await service.update_review(db=db, review_id=review_id, review_update=review_update)
    if not db_review:
        raise HTTPException(status_code=400, detail="Изменения не применены")
    
    review_out = Review.model_validate(db_review)
    
    await cache.redis.delete(f"review:{review_id}")
    await cache.invalidate_pattern("reviews:all")
    await cache.redis.delete(f"reviews:user:{current_user.user_id}")
    
    return review_out

# Удаление отзыва
@router.delete("/{review_id}", response_model=Review)
async def delete_review(review_id: int, 
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user),
                        cache: CacheManager = Depends(get_cache_manager)) -> Review:
    existing_review = await service.get_review_by_id(db=db, review_id=review_id)
    if not existing_review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    user_id = existing_review.user_id
    
    if current_user.role == "Admin":
        db_review = await service.delete_review(db=db, review_id=review_id)
        if not db_review:
            raise HTTPException(status_code=404, detail="Отзыв не найден")

    elif current_user.role == "Client":
        if existing_review.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Вы можете удалить только свой отзыв")

        db_review = await service.delete_review(db=db, review_id=review_id)

    else:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    review_out = Review.model_validate(db_review)
    
    await cache.redis.delete(f"review:{review_id}")
    await cache.invalidate_pattern("reviews:all")
    await cache.redis.delete(f"reviews:user:{user_id}")
    
    return review_out

# Ответ на отзыв
@router.post("/{review_id}/response", response_model=Review)
async def respond_to_review(review_id: int, 
                            response_data: AdminReviewResponse, 
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user),
                            cache: CacheManager = Depends(get_cache_manager)) -> Review:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут отвечать на отзывы")
    try:
        db_review = await service.respond_to_review(db=db, review_id=review_id, response=response_data.admin_response)
        
        review_out = Review.model_validate(db_review)
        
        await cache.redis.delete(f"review:{review_id}")
        await cache.invalidate_pattern("reviews:all")
        await cache.redis.delete(f"reviews:user:{db_review.user_id}")
        
        return review_out
    except ValueError:
        raise HTTPException(status_code=404, detail="Отзыв не найден")