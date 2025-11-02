import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.cache import CacheManager, get_cache_manager
from app.models.user import User
from app.services import user_service
from app.schemas import user as user_schema
from app.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["Пользователи"])

# Получение всех пользователей
@router.get("/", response_model=list[user_schema.UserOut])
async def get_users(db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    cache: CacheManager = Depends(get_cache_manager)
                    ) -> List[User]:
    start_time = time.time()

    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    cache_key = "users:all"
    cached_users = await cache.get_cached(cache_key)
    if cached_users:
        print(f"[REDIS] All users from cache - {time.time() - start_time:.3f}s")
        return cached_users
    
    users = await user_service.get_all_users(db)
    db_time = time.time() - start_time
    print(f"[REDIS] All users from database - {db_time:.3f}s")
    
    await cache.set_cached(cache_key, [user.model_dump() for user in users], ttl=1800)
    
    return users

# Получение информации о своем аккаунте
@router.get("/me", response_model=user_schema.UserOut)
async def get_my_user_data(current_user: User = Depends(get_current_user), 
                           db: AsyncSession = Depends(get_db),
                           cache: CacheManager = Depends(get_cache_manager)) -> User:
    start_time = time.time()
    cache_key = f"user:me:{current_user.user_id}"

    cached_user = await cache.get_cached(cache_key)
    if cached_user:
        print(f"[REDIS] My user data from cache - {time.time() - start_time:.3f}s")
        return cached_user

    user = await user_service.get_user_by_id(current_user.user_id, db)
    db_time = time.time() - start_time
    print(f"[REDIS] My user data from database - {db_time:.3f}s")

    user_out = user_schema.UserOut.model_validate(user)
    await cache.set_cached(cache_key, user_out.model_dump(), ttl=3600)
    
    return user

# Создание пользователя
@router.post("/", response_model=user_schema.UserOut, status_code=201)
async def create_user(user: user_schema.UserCreate, 
                      db: AsyncSession = Depends(get_db),
                      cache: CacheManager = Depends(get_cache_manager)) -> User:
    created_user = await user_service.create_user(user, db)

    await cache.invalidate_pattern("users:all")
    await cache.invalidate_pattern(f"users:role:*")

    return created_user

# Удаление собственного аккаунта — для любого пользователя
@router.delete("/me", status_code=204)
async def delete_own_account(db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(get_current_user),
                             cache: CacheManager = Depends(get_cache_manager)) -> None:
    user_to_delete = await user_service.get_user_by_id(current_user.user_id, db)

    await user_service.delete_user(current_user.user_id, db)

    if user_to_delete:
        await cache.redis.delete(f"user:me:{current_user.user_id}")
        await cache.invalidate_pattern("users:all")
        await cache.redis.delete(f"users:role:{user_to_delete.role}")

# Удаление любого пользователя по ID — только для админа
@router.delete("/{user_id}", status_code=204)
async def delete_user_by_admin(user_id: int, 
                               db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user),
                               cache: CacheManager = Depends(get_cache_manager)) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    user_to_delete = await user_service.get_user_by_id(user_id, db)
    
    await user_service.delete_user(user_id, db)
    
    await cache.redis.delete(f"user:me:{user_id}")
    await cache.invalidate_pattern("users:all")
    await cache.redis.delete(f"users:role:{user_to_delete.role}")

# Получение пользователей с заданной ролью
@router.get("/role/{role}", response_model=list[user_schema.UserOut])
async def get_users_by_role(role: str, 
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user),
                            cache: CacheManager = Depends(get_cache_manager)) -> List[User]:
    start_time = time.time()

    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    valid_roles = [r.value for r in user_schema.UserRole]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail="Неверная роль пользователя")
    
    cache_key = f"users:role:{role}"
    
    cached_users = await cache.get_cached(cache_key)
    if cached_users:
        print(f"[REDIS] Users by role from cache - {time.time() - start_time:.3f}s")
        return cached_users
    
    users = await user_service.get_users_by_role(role, db)
    db_time = time.time() - start_time
    print(f"[REDIS] Users by role from database - {db_time:.3f}s")

    await cache.set_cached(cache_key, [user.model_dump() for user in users], ttl=1800)

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
                           current_user: User = Depends(get_current_user),
                           cache: CacheManager = Depends(get_cache_manager)) -> User:
    updated_user = await user_service.update_user_data(current_user.user_id, user_data, db)

    await cache.redis.delete(f"user:me:{current_user.user_id}")
    await cache.invalidate_pattern("users:all")
    await cache.invalidate_pattern(f"users:role:{current_user.role}")

    return updated_user