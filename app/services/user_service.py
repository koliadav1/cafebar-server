from typing import List
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.schemas.user import UserCreate, UserPasswordUpdate, UserUpdate
from app.services.auth_service import verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Получить всех пользователей
def get_all_users(db: Session) -> List[User]:
    return db.query(User).all()

# Получить одного пользователя по ID
def get_user_by_id(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# Создание нового пользователя (регистрация)
def create_user(user_data: UserCreate, db: Session) -> User:
    existing_user = db.query(User).filter(User.email == user_data.email).first()
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
    db.commit()
    db.refresh(new_user)
    return new_user

# Удаление пользователя
def delete_user(user_id: int, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    db.delete(user)
    db.commit()
    return {"detail": "Пользователь успешно удалён"}

# Получить всех пользователей с определенной ролью
def get_users_by_role(role: str, db: Session) -> List[User]:
    return db.query(User).filter(User.role == role).all()

# Изменить пароль
def update_user_password(user_id: int, password_data: UserPasswordUpdate, db: Session) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    old_hash = password_data.old_password
    if not verify_password(old_hash, user.password_hash):
        raise HTTPException(status_code=403, detail="Неверный старый пароль")

    user.password_hash = pwd_context.hash(password_data.new_password)
    db.commit()
    db.refresh(user)
    return user

# Изменить свои данные
def update_user_data(user_id: int, user_data: UserUpdate, db: Session) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    for field, value in user_data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user