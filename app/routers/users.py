import asyncio

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.services import user_service
from app.schemas import user as user_schema
from app.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["Пользователи"])

# Получение всех пользователей
@router.get("/", response_model=list[user_schema.UserOut])
async def get_users(db: Session = Depends(get_db), 
                    current_user: User = Depends(get_current_user)) -> List[User]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    return await asyncio.to_thread(user_service.get_all_users, db)

# Получение информации о своем аккаунте
@router.get("/me", response_model=user_schema.UserOut)
async def get_my_user_data(current_user: User = Depends(get_current_user), 
                           db: Session = Depends(get_db)) -> User:
    user = await asyncio.to_thread(user_service.get_user_by_id, current_user.user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# Создание пользователя
@router.post("/", response_model=user_schema.UserOut, status_code=201)
async def create_user(user: user_schema.UserCreate, 
                      db: Session = Depends(get_db)) -> User:
    created_user = await asyncio.to_thread(user_service.create_user, user, db)
    return created_user

# Удаление собственного аккаунта — для любого пользователя
@router.delete("/me", status_code=204)
async def delete_own_account(db: Session = Depends(get_db), 
                             current_user: User = Depends(get_current_user)) -> None:
    success = await asyncio.to_thread(user_service.delete_user, current_user.user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

# Удаление любого пользователя по ID — только для админа
@router.delete("/{user_id}", status_code=204)
async def delete_user_by_admin(user_id: int, 
                               db: Session = Depends(get_db), 
                               current_user: User = Depends(get_current_user)) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    success = await asyncio.to_thread(user_service.delete_user, user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

# Получение пользователей с заданной ролью
@router.get("/role/{role}", response_model=list[user_schema.UserOut])
async def get_users_by_role(role: str, 
                            db: Session = Depends(get_db), 
                            current_user: User = Depends(get_current_user)) -> List[User]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    valid_roles = [r.value for r in user_schema.UserRole]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail="Неверная роль пользователя")

    users = await asyncio.to_thread(user_service.get_users_by_role, role, db)
    return users

# Изменение пароля текущего пользователя
@router.put("/me/password", response_model=user_schema.UserOut)
async def change_password(password_data: user_schema.UserPasswordUpdate, 
                          db: Session = Depends(get_db), 
                          current_user: User = Depends(get_current_user)) -> User:
    updated_user = await asyncio.to_thread(user_service.update_user_password, current_user.user_id, password_data, db)
    return updated_user

# Обновление данных пользователя (email, телефон, username)
@router.put("/me", response_model=user_schema.UserOut)
async def update_user_data(user_data: user_schema.UserUpdate, 
                           db: Session = Depends(get_db), 
                           current_user: User = Depends(get_current_user)) -> User:
    updated_user = await asyncio.to_thread(user_service.update_user_data, current_user.user_id, user_data, db)
    return updated_user