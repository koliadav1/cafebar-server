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

router = APIRouter(prefix="/recommendations", tags=["Рекомендации"])

# Получение популярных блюд ресторана
@router.get("/popular", response_model=list[RecommendedItem])
async def popular_items(limit: int = 5, db: AsyncSession = Depends(get_db)) -> list[RecommendedItem]:
    return await get_most_popular_items(db=db, limit=limit)

# Получение ваших любимых блюд
@router.get("/personal", response_model=list[RecommendedItem])
async def personal_recommendations(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)) -> list[RecommendedItem]:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только клиенты получают персональные рекомендации"
        )
    return await get_user_recommendations(user_id=current_user.user_id, db=db, limit=limit)

# Получение популярных напитков ресторана
@router.get("/drinks/popular", response_model=list[RecommendedItem])
async def popular_drinks(limit: int = 5, db: AsyncSession = Depends(get_db)) -> list[RecommendedItem]:
    return await get_most_popular_drinks(db=db, limit=limit)

# Получение ваших любимых напитков
@router.get("/drinks/personal", response_model=list[RecommendedItem])
async def personal_drink_recommendations(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)) -> list[RecommendedItem]:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только клиенты получают персональные рекомендации"
        )
    return await get_user_drink_recommendations(user_id=current_user.user_id, db=db, limit=limit)