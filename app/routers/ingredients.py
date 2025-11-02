import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.cache import CacheManager, get_cache_manager
from app.models.user import User
from app.services import ingredients_service
from app.schemas.ingredient import MenuItemIngredientCreate, MenuItemIngredientOut
from app.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/menu-item-ingredients", tags=["Состав позиции меню"])

# Получение игнгредиентов позиции меню
@router.get("/{item_id}", response_model=list[MenuItemIngredientOut])
async def get_menu_item_ingredients(item_id: int, 
                                    db: AsyncSession = Depends(get_db),
                                    cache: CacheManager = Depends(get_cache_manager)) -> list[MenuItemIngredientOut]:
    start_time = time.time()
    cache_key = f"ingredients:menu_item:{item_id}"
    
    cached_ingredients = await cache.get_cached(cache_key)
    if cached_ingredients:
        print(f"[REDIS] Ingredients from cache - {time.time() - start_time:.3f}s")
        return cached_ingredients

    ingredients = await ingredients_service.get_ingredients_by_item_id(item_id, db)
    db_time = time.time() - start_time
    print(f"[REDIS] Ingredients from database - {db_time:.3f}s")
    if not ingredients:
        raise HTTPException(status_code=404, detail="Состав позиции меню не найден")
    
    ingredients_out = [MenuItemIngredientOut.model_validate(ingredient) for ingredient in ingredients]
    await cache.set_cached(cache_key, [ingredient.model_dump() for ingredient in ingredients_out], ttl=7200)
    
    return ingredients_out

# Добавление ингредиента в позицию меню
@router.post("/{item_id}", response_model=MenuItemIngredientOut)
async def create_menu_item_ingredient(item_id: int, 
                                      ingredient: MenuItemIngredientCreate, 
                                      db: AsyncSession = Depends(get_db),
                                      current_user: User = Depends(get_current_user),
                                      cache: CacheManager = Depends(get_cache_manager)) -> MenuItemIngredientOut:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут добавлять ингредиенты в позиции меню")
    ingredient_obj = await ingredients_service.create_menu_item_ingredient(item_id, ingredient, db)
    ingredient_out = MenuItemIngredientOut.model_validate(ingredient_obj)
    
    await cache.redis.delete(f"ingredients:menu_item:{item_id}")
    await cache.invalidate_pattern("ingredients:all")
    await cache.redis.delete(f"menu:item:{item_id}")
    await cache.invalidate_pattern("menu:all:*")
    
    return ingredient_out

# Удаление ингердиента из позиции меню
@router.delete("/{item_id}/{ingredient_id}", status_code=204)
async def delete_menu_item_ingredient(item_id: int, 
                                      ingredient_id: int, 
                                      db: AsyncSession = Depends(get_db),
                                      current_user: User = Depends(get_current_user),
                                      cache: CacheManager = Depends(get_cache_manager)) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут удалять ингредиенты из позиций меню")
    await ingredients_service.delete_menu_item_ingredient(item_id, ingredient_id, db)
    
    await cache.redis.delete(f"ingredients:menu_item:{item_id}")
    await cache.invalidate_pattern("ingredients:all")
    await cache.redis.delete(f"menu:item:{item_id}")
    await cache.invalidate_pattern("menu:all:*")
    
    return None

# Получение всех ингредиентов
@router.get("/", response_model=list[MenuItemIngredientOut])
async def get_all_menu_item_ingredients(db: AsyncSession = Depends(get_db), 
                                        cache: CacheManager = Depends(get_cache_manager)) -> list[MenuItemIngredientOut]:
    start_time = time.time()
    cache_key = "ingredients:all"
    
    cached_ingredients = await cache.get_cached(cache_key)
    if cached_ingredients:
        print(f"[REDIS] All ingredients from cache - {time.time() - start_time:.3f}s")
        return cached_ingredients

    ingredients = await ingredients_service.get_all_menu_item_ingredients(db)
    db_time = time.time() - start_time
    print(f"[REDIS] All ingredients from database - {db_time:.3f}s")

    ingredients_out = [MenuItemIngredientOut.model_validate(ingredient) for ingredient in ingredients]
    await cache.set_cached(cache_key, [ingredient.model_dump() for ingredient in ingredients_out], ttl=14400)
    
    return ingredients_out