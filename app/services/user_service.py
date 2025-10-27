from typing import List
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.user import User
from app.schemas.user import UserCreate, UserPasswordUpdate, UserUpdate
from app.services.auth_service import verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Получить всех пользователей
async def get_all_users(db: AsyncSession) -> List[User]:
    result = await db.execute(select(User))
    return result.scalars().all()

# Получить одного пользователя по ID
async def get_user_by_id(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# Создание нового пользователя (регистрация)
async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    hashed_password = pwd_context.hash(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password_hash=hashed_password,
        role=user_data.role,
        created_at=user_data.created_at
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Удаление пользователя
async def delete_user(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    await db.delete(user)
    await db.commit()
    return {"detail": "Пользователь успешно удалён"}

# Получить всех пользователей с определенной ролью
async def get_users_by_role(role: str, db: AsyncSession) -> List[User]:
    result = await db.execute(select(User).where(User.role == role))
    return result.scalars().all()

# Изменить пароль
async def update_user_password(user_id: int, password_data: UserPasswordUpdate, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if not verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(status_code=403, detail="Неверный старый пароль")

    user.password_hash = pwd_context.hash(password_data.new_password)
    await db.commit()
    await db.refresh(user)
    return user

# Изменить свои данные
async def update_user_data(user_id: int, user_data: UserUpdate, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user