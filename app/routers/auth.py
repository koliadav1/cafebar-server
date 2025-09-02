import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import login_user, create_access_token
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Логин"])

#Вход
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = await asyncio.to_thread(login_user, data, db)
    if not user:
        raise HTTPException(status_code=400, detail="Неправильные данных для входа")
    token = create_access_token(data={"sub": user.username, "user_id": user.user_id, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}