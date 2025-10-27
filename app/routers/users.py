from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services import user_service
from app.schemas import user as user_schema
from app.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["Пользователи"])

# Получение всех пользователей
@router.get("/", response_model=list[user_schema.UserOut])
async def get_users(db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)) -> List[User]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    return await user_service.get_all_users(db)

# Получение информации о своем аккаунте
@router.get("/me", response_model=user_schema.UserOut)
async def get_my_user_data(current_user: User = Depends(get_current_user), 
                           db: AsyncSession = Depends(get_db)) -> User:
    user = await user_service.get_user_by_id(current_user.user_id, db)
    return user

# Создание пользователя
@router.post("/", response_model=user_schema.UserOut, status_code=201)
async def create_user(user: user_schema.UserCreate, 
                      db: AsyncSession = Depends(get_db)) -> User:
    created_user = await user_service.create_user(user, db)
    return created_user

# Удаление собственного аккаунта — для любого пользователя
@router.delete("/me", status_code=204)
async def delete_own_account(db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(get_current_user)) -> None:
    await user_service.delete_user(current_user.user_id, db)

# Удаление любого пользователя по ID — только для админа
@router.delete("/{user_id}", status_code=204)
async def delete_user_by_admin(user_id: int, 
                               db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user)) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    await user_service.delete_user(user_id, db)

# Получение пользователей с заданной ролью
@router.get("/role/{role}", response_model=list[user_schema.UserOut])
async def get_users_by_role(role: str, 
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user)) -> List[User]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    valid_roles = [r.value for r in user_schema.UserRole]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail="Неверная роль пользователя")

    users = await user_service.get_users_by_role(role, db)
    return users

# Изменение пароля текущего пользователя
@router.put("/me/password", response_model=user_schema.UserOut)
async def change_password(password_data: user_schema.UserPasswordUpdate, 
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)) -> User:
    updated_user = await user_service.update_user_password(current_user.user_id, password_data, db)
    return updated_user

# Обновление данных пользователя (email, телефон, username)
@router.put("/me", response_model=user_schema.UserOut)
async def update_user_data(user_data: user_schema.UserUpdate, 
                           db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)) -> User:
    updated_user = await user_service.update_user_data(current_user.user_id, user_data, db)
    return updated_user