import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.recommendation import RecommendedItem
from app.services.auth_service import get_current_user
from app.services.recommendation_service import (
    get_most_popular_items,
    get_user_recommendations,
    get_most_popular_drinks,
    get_user_drink_recommendations
)
from app.dependencies.cache import get_cache_manager, CacheManager

router = APIRouter(prefix="/recommendations", tags=["Рекомендации"])

# Получение популярных блюд ресторана
@router.get("/popular", response_model=list[RecommendedItem])
async def popular_items(
    limit: int = 5, 
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager)
) -> list[RecommendedItem]:
    start_time = time.time()
    cache_key = f"recommendations:popular:limit:{limit}"
    
    cached_recommendations = await cache.get_cached(cache_key)
    if cached_recommendations:
        print(f"[REDIS] Popular recommendations from cache - {time.time() - start_time:.3f}s")
        return cached_recommendations
    
    recommendations = await get_most_popular_items(db=db, limit=limit)
    db_time = time.time() - start_time
    print(f"[REDIS] Popular recommendations from database - {db_time:.3f}s")
    
    await cache.set_cached(cache_key, [item.model_dump() for item in recommendations], ttl=600)
    
    return recommendations

# Получение ваших любимых блюд
@router.get("/personal", response_model=list[RecommendedItem])
async def personal_recommendations(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cache: CacheManager = Depends(get_cache_manager)
) -> list[RecommendedItem]:
    start_time = time.time()
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только клиенты получают персональные рекомендации"
        )
    
    cache_key = f"recommendations:personal:{current_user.user_id}:limit:{limit}"
    
    cached_recommendations = await cache.get_cached(cache_key)
    if cached_recommendations:
        print(f"[REDIS] Personal recommendations from cache - {time.time() - start_time:.3f}s")
        return cached_recommendations

    recommendations = await get_user_recommendations(user_id=current_user.user_id, db=db, limit=limit)
    db_time = time.time() - start_time
    print(f"[REDIS] Personal recommendations from database - {db_time:.3f}s")

    await cache.set_cached(cache_key, [item.model_dump() for item in recommendations], ttl=300)
    
    return recommendations

# Получение популярных напитков ресторана
@router.get("/drinks/popular", response_model=list[RecommendedItem])
async def popular_drinks(
    limit: int = 5, 
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager)
) -> list[RecommendedItem]:
    start_time = time.time()
    cache_key = f"recommendations:drinks:popular:limit:{limit}"
    
    cached_recommendations = await cache.get_cached(cache_key)
    if cached_recommendations:
        print(f"[REDIS] Popular drinks from cache - {time.time() - start_time:.3f}s")
        return cached_recommendations
    
    recommendations = await get_most_popular_drinks(db=db, limit=limit)
    db_time = time.time() - start_time
    print(f"[REDIS] Popular drinks from database - {db_time:.3f}s")

    await cache.set_cached(cache_key, [item.model_dump() for item in recommendations], ttl=600)
    
    return recommendations

# Получение ваших любимых напитков
@router.get("/drinks/personal", response_model=list[RecommendedItem])
async def personal_drink_recommendations(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cache: CacheManager = Depends(get_cache_manager)
) -> list[RecommendedItem]:
    start_time = time.time()
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только клиенты получают персональные рекомендации"
        )
    
    cache_key = f"recommendations:drinks:personal:{current_user.user_id}:limit:{limit}"
    
    cached_recommendations = await cache.get_cached(cache_key)
    if cached_recommendations:
        print(f"[REDIS] Personal drinks from cache - {time.time() - start_time:.3f}s")
        return cached_recommendations
    
    recommendations = await get_user_drink_recommendations(user_id=current_user.user_id, db=db, limit=limit)
    db_time = time.time() - start_time
    print(f"[REDIS] Personal drinks from database - {db_time:.3f}s")

    await cache.set_cached(cache_key, [item.model_dump() for item in recommendations], ttl=300)
    
    return recommendations