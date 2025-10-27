from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.menu_item_ingredients import MenuItemIngredient
from app.models.ingredients import Ingredient
from app.schemas.ingredient import IngredientOut, MenuItemIngredientCreate, MenuItemIngredientOut

# Получить состав позиции меню по item_id
async def get_ingredients_by_item_id(item_id: int, db: AsyncSession) -> list[MenuItemIngredientOut]:
    result = await db.execute(
        select(MenuItemIngredient).where(MenuItemIngredient.item_id == item_id)
    )
    menu_item_ingredients = result.scalars().all()
    result_list = []

    for item_ingredient in menu_item_ingredients:
        ingredient_result = await db.execute(
            select(Ingredient).where(Ingredient.ingredient_id == item_ingredient.ingredient_id)
        )
        ingredient = ingredient_result.scalar_one_or_none()
        
        if ingredient:
            result_list.append(MenuItemIngredientOut(
                item_id=item_ingredient.item_id,
                ingredient=IngredientOut(
                    ingredient_id=ingredient.ingredient_id,
                    name=ingredient.name,
                    unit=ingredient.unit
                ),
                required_quantity=item_ingredient.required_quantity
            ))
    return result_list

# Добавление ингредиента в состав позиции меню
async def create_menu_item_ingredient(item_id: int, ingredient_data: MenuItemIngredientCreate, db: AsyncSession) -> MenuItemIngredientOut:
    ingredient_result = await db.execute(
        select(Ingredient).where(Ingredient.name == ingredient_data.ingredient.name)
    )
    existing_ingredient = ingredient_result.scalar_one_or_none()
    
    if not existing_ingredient:
        new_ingredient = Ingredient(
            name=ingredient_data.ingredient.name,
            unit=ingredient_data.ingredient.unit,
            quantity=ingredient_data.ingredient.quantity,
            threshold=ingredient_data.ingredient.threshold
        )
        db.add(new_ingredient)
        await db.commit()
        await db.refresh(new_ingredient)
        existing_ingredient = new_ingredient

    new_menu_item_ingredient = MenuItemIngredient(
        item_id=item_id,
        ingredient_id=existing_ingredient.ingredient_id,
        required_quantity=ingredient_data.required_quantity
    )

    db.add(new_menu_item_ingredient)
    await db.commit()
    await db.refresh(new_menu_item_ingredient)

    return MenuItemIngredientOut(
        item_id=new_menu_item_ingredient.item_id,
        ingredient=IngredientOut(
            ingredient_id=existing_ingredient.ingredient_id,
            name=existing_ingredient.name,
            unit=existing_ingredient.unit
        ),
        required_quantity=new_menu_item_ingredient.required_quantity
    )

# Удалить ингредиент из состава позиции меню
async def delete_menu_item_ingredient(item_id: int, ingredient_id: int, db: AsyncSession):
    result = await db.execute(
        select(MenuItemIngredient).where(
            MenuItemIngredient.item_id == item_id,
            MenuItemIngredient.ingredient_id == ingredient_id
        )
    )
    menu_item_ingredient = result.scalar_one_or_none()

    if not menu_item_ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден в составе позиции меню")

    await db.delete(menu_item_ingredient)
    await db.commit()
    return {"detail": "Ингредиент удален из состава позиции меню"}

# Получить все составы всех позиций меню
async def get_all_menu_item_ingredients(db: AsyncSession) -> list[MenuItemIngredientOut]:
    result = await db.execute(select(MenuItemIngredient))
    menu_item_ingredients = result.scalars().all()
    result_list = []

    for item_ingredient in menu_item_ingredients:
        ingredient_result = await db.execute(
            select(Ingredient).where(Ingredient.ingredient_id == item_ingredient.ingredient_id)
        )
        ingredient = ingredient_result.scalar_one_or_none()
        
        if ingredient:
            result_list.append(MenuItemIngredientOut(
                item_id=item_ingredient.item_id,
                ingredient=IngredientOut(
                    ingredient_id=ingredient.ingredient_id,
                    name=ingredient.name,
                    unit=ingredient.unit
                ),
                required_quantity=item_ingredient.required_quantity
            ))

    return result_list