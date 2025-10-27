from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services import ingredients_service
from app.schemas.ingredient import MenuItemIngredientCreate, MenuItemIngredientOut
from app.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/menu-item-ingredients", tags=["Состав позиции меню"])

# Получение игнгредиентов позиции меню
@router.get("/{item_id}", response_model=list[MenuItemIngredientOut])
async def get_menu_item_ingredients(item_id: int, db: AsyncSession = Depends(get_db)) -> list[MenuItemIngredientOut]:
    ingredients = await ingredients_service.get_ingredients_by_item_id(item_id, db)
    if not ingredients:
        raise HTTPException(status_code=404, detail="Состав позиции меню не найден")
    return ingredients

# Добавление ингредиента в позицию меню
@router.post("/{item_id}", response_model=MenuItemIngredientOut)
async def create_menu_item_ingredient(item_id: int, 
                                      ingredient: MenuItemIngredientCreate, 
                                      db: AsyncSession = Depends(get_db),
                                      current_user: User = Depends(get_current_user)) -> MenuItemIngredientOut:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут добавлять ингредиенты в позиции меню")
    ingredient_obj = await ingredients_service.create_menu_item_ingredient(item_id, ingredient, db)
    return ingredient_obj

# Удаление ингердиента из позиции меню
@router.delete("/{item_id}/{ingredient_id}", status_code=204)
async def delete_menu_item_ingredient(item_id: int, 
                                      ingredient_id: int, 
                                      db: AsyncSession = Depends(get_db),
                                      current_user: User = Depends(get_current_user)) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут удалять ингредиенты из позиций меню")
    await ingredients_service.delete_menu_item_ingredient(item_id, ingredient_id, db)
    return None

# Получение всех ингредиентов
@router.get("/", response_model=list[MenuItemIngredientOut])
async def get_all_menu_item_ingredients(db: AsyncSession = Depends(get_db)) -> list[MenuItemIngredientOut]:
    return await ingredients_service.get_all_menu_item_ingredients(db)