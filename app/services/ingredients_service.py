from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.menu_item_ingredients import MenuItemIngredient
from app.models.ingredients import Ingredient
from app.schemas.ingredient import IngredientOut, MenuItemIngredientCreate, MenuItemIngredientOut

# Получить состав позиции меню по item_id
def get_ingredients_by_item_id(item_id: int, db: Session) -> list[MenuItemIngredientOut]:
    menu_item_ingredients = db.query(MenuItemIngredient).filter(MenuItemIngredient.item_id == item_id).all()
    result = []

    for item_ingredient in menu_item_ingredients:
        ingredient = db.query(Ingredient).filter(Ingredient.ingredient_id == item_ingredient.ingredient_id).first()
        if ingredient:
            result.append(MenuItemIngredientOut(
                item_id=item_ingredient.item_id,
                ingredient=IngredientOut(
                    ingredient_id=ingredient.ingredient_id,
                    name=ingredient.name,
                    unit=ingredient.unit
                ),
                required_quantity=item_ingredient.required_quantity
            ))
    return result

# Добавление ингредиента в состав позиции меню
def create_menu_item_ingredient(item_id: int, ingredient_data: MenuItemIngredientCreate, db: Session) -> MenuItemIngredientOut:
    existing_ingredient = db.query(Ingredient).filter(Ingredient.name == ingredient_data.ingredient.name).first()
    if not existing_ingredient:
        new_ingredient = Ingredient(
            name=ingredient_data.ingredient.name,
            unit=ingredient_data.ingredient.unit,
            quantity=ingredient_data.ingredient.quantity,
            threshold=ingredient_data.ingredient.threshold
        )
        db.add(new_ingredient)
        db.commit()
        db.refresh(new_ingredient)
        existing_ingredient = new_ingredient

    new_menu_item_ingredient = MenuItemIngredient(
        item_id=item_id,
        ingredient_id=existing_ingredient.ingredient_id,
        required_quantity=ingredient_data.required_quantity
    )

    db.add(new_menu_item_ingredient)
    db.commit()
    db.refresh(new_menu_item_ingredient)

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
def delete_menu_item_ingredient(item_id: int, ingredient_id: int, db: Session):
    menu_item_ingredient = db.query(MenuItemIngredient).filter(
        MenuItemIngredient.item_id == item_id,
        MenuItemIngredient.ingredient_id == ingredient_id
    ).first()

    if not menu_item_ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден в составе позиции меню")

    db.delete(menu_item_ingredient)
    db.commit()
    return {"detail": "Ингредиент удален из состава позиции меню"}

# Получить все составы всех позиций меню
def get_all_menu_item_ingredients(db: Session) -> list[MenuItemIngredientOut]:
    menu_item_ingredients = db.query(MenuItemIngredient).all()
    result = []

    for item_ingredient in menu_item_ingredients:
        ingredient = db.query(Ingredient).filter(Ingredient.ingredient_id == item_ingredient.ingredient_id).first()
        if ingredient:
            result.append(MenuItemIngredientOut(
                item_id=item_ingredient.item_id,
                ingredient=IngredientOut(
                    ingredient_id=ingredient.ingredient_id,
                    name=ingredient.name,
                    unit=ingredient.unit
                ),
                required_quantity=item_ingredient.required_quantity
            ))

    return result