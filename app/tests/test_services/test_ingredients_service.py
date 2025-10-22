import pytest
from decimal import Decimal
from fastapi import HTTPException

from app.services.ingredients_service import (
    get_ingredients_by_item_id,
    create_menu_item_ingredient,
    delete_menu_item_ingredient,
    get_all_menu_item_ingredients
)
from app.models.ingredients import Ingredient


class TestIngredientsService:
    # Тест получения ингредиентов по ID позиции меню
    def test_get_ingredients_by_item_id_success(self, test_db, sample_ingredient):
        from app.models.menu_item_ingredients import MenuItemIngredient

        menu_item_ingredient = MenuItemIngredient(
            item_id=1,
            ingredient_id=sample_ingredient.ingredient_id,
            required_quantity=Decimal("200.0")
        )
        test_db.add(menu_item_ingredient)
        test_db.commit()

        result = get_ingredients_by_item_id(1, test_db)
        assert len(result) == 1
        assert result[0].item_id == 1
        assert result[0].ingredient.name == sample_ingredient.name
        assert result[0].required_quantity == Decimal("200.0")

    # Тест получения ингредиентов для несуществующей позиции
    def test_get_ingredients_by_item_id_not_found(self, test_db):
        result = get_ingredients_by_item_id(999, test_db)
        assert len(result) == 0

    # Тест создания связи с новым ингредиентом
    def test_create_menu_item_ingredient_new_ingredient(self, test_db, sample_ingredient_data):
        """Тест создания связи с новым ингредиентом"""
        from app.schemas.ingredient import MenuItemIngredientCreate
        
        ingredient_data = MenuItemIngredientCreate(**sample_ingredient_data)
        
        result = create_menu_item_ingredient(1, ingredient_data, test_db)

        assert result.item_id == 1
        assert result.ingredient.name == sample_ingredient_data["ingredient"]["name"]
        assert result.required_quantity == sample_ingredient_data["required_quantity"]

        db_ingredient = test_db.query(Ingredient).filter(
            Ingredient.name == sample_ingredient_data["ingredient"]["name"]
        ).first()
        assert db_ingredient is not None

    # Тест создания связи с существующим ингредиентом
    def test_create_menu_item_ingredient_existing_ingredient(self, test_db, sample_ingredient):
        from app.schemas.ingredient import MenuItemIngredientCreate, IngredientCreate
        
        ingredient_data = MenuItemIngredientCreate(
            ingredient=IngredientCreate(
                name=sample_ingredient.name,
                unit=sample_ingredient.unit,
                quantity=float(sample_ingredient.quantity),
                threshold=float(sample_ingredient.threshold)
            ),
            required_quantity=Decimal("1.0")
        )

        result = create_menu_item_ingredient(1, ingredient_data, test_db)

        assert result.item_id == 1
        assert result.ingredient.ingredient_id == sample_ingredient.ingredient_id
        assert result.required_quantity == Decimal("1.0")

    # Тест удаления связи ингредиента с позицией меню
    def test_delete_menu_item_ingredient_success(self, test_db, sample_ingredient):
        from app.models.menu_item_ingredients import MenuItemIngredient

        menu_item_ingredient = MenuItemIngredient(
            item_id=1,
            ingredient_id=sample_ingredient.ingredient_id,
            required_quantity=Decimal("2.0")
        )
        test_db.add(menu_item_ingredient)
        test_db.commit()

        result = delete_menu_item_ingredient(1, sample_ingredient.ingredient_id, test_db)

        assert result == {"detail": "Ингредиент удален из состава позиции меню"}

        db_relation = test_db.query(MenuItemIngredient).filter(
            MenuItemIngredient.item_id == 1,
            MenuItemIngredient.ingredient_id == sample_ingredient.ingredient_id
        ).first()
        assert db_relation is None

    # Тест удаления несуществующей связи
    def test_delete_menu_item_ingredient_not_found(self, test_db):
        with pytest.raises(HTTPException) as exc_info:
            delete_menu_item_ingredient(1, 999, test_db)
        assert exc_info.value.status_code == 404
        assert "Ингредиент не найден" in str(exc_info.value.detail)

    # Тест получения всех связей ингредиентов
    def test_get_all_menu_item_ingredients(self, test_db, sample_ingredient):
        from app.models.menu_item_ingredients import MenuItemIngredient

        menu_item_ingredient = MenuItemIngredient(
            item_id=1,
            ingredient_id=sample_ingredient.ingredient_id,
            required_quantity=Decimal("200.0")
        )
        test_db.add(menu_item_ingredient)
        test_db.commit()

        result = get_all_menu_item_ingredients(test_db)

        assert len(result) == 1
        assert result[0].item_id == 1
        assert result[0].ingredient.name == sample_ingredient.name