from sqlalchemy import Column, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

from app.config import Config
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Проверка пароля
def verify_password(plain_password: str, hashed_password: Column[str]) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Логин
async def login_user(data: LoginRequest, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    return user

# Создание веб-токена
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.HASH_SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt

# Получение своих данных
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, Config.HASH_SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Неправильный токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Не удалось подтвердить данные")

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user