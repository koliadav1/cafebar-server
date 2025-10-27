import pytest
from unittest.mock import patch


class TestIngredientsRouter:
    # Тест получения ингредиентов позиции меню
    @pytest.mark.asyncio
    async def test_get_menu_item_ingredients_success(self, client, test_db, sample_ingredient):
        from app.models.menu_item_ingredients import MenuItemIngredient
        from decimal import Decimal

        menu_item_ingredient = MenuItemIngredient(
            item_id=1,
            ingredient_id=sample_ingredient.ingredient_id,
            required_quantity=Decimal("200.0")
        )
        test_db.add(menu_item_ingredient)
        await test_db.commit()

        response = await client.get("/menu-item-ingredients/1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["item_id"] == 1
        assert data[0]["ingredient"]["name"] == sample_ingredient.name

    # Тест получения ингредиентов несуществующей позиции
    @pytest.mark.asyncio
    async def test_get_menu_item_ingredients_not_found(self, client):
        response = await client.get("/menu-item-ingredients/999")
        
        assert response.status_code == 404
        assert "Состав позиции меню не найден" in response.json()["detail"]

    # Тест создания связи ингредиента с позицией меню админом
    @pytest.mark.asyncio
    async def test_create_menu_item_ingredient_as_admin(self, admin_client, test_db):
        """Тест создания связи ингредиента с позицией меню админом"""
        ingredient_data = {
            "ingredient": {
                "name": "Новый ингредиент",
                "unit": "кг", 
                "quantity": 5.0,
                "threshold": 1.0
            },
            "required_quantity": 0.5
        }

        response = await admin_client.post("/menu-item-ingredients/1", json=ingredient_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == 1
        assert data["ingredient"]["name"] == "Новый ингредиент"
        assert float(data["required_quantity"]) == 0.5
        
        from app.models.ingredients import Ingredient
        from sqlalchemy import select
        result = await test_db.execute(select(Ingredient).filter(Ingredient.name == "Новый ингредиент"))
        db_ingredient = result.scalar_one_or_none()
        assert db_ingredient is not None

    # Тест создания связи ингредиента без прав админа
    @pytest.mark.asyncio
    async def test_create_menu_item_ingredient_as_non_admin(self, authenticated_client):
        ingredient_data = {
            "ingredient": {
                "name": "Новый ингредиент",
                "unit": "кг",
                "quantity": 5.0,
                "threshold": 1.0
            },
            "required_quantity": 0.5
        }

        response = await authenticated_client.post("/menu-item-ingredients/1", json=ingredient_data)

        assert response.status_code == 403
        assert "Только админы могут добавлять ингредиенты" in response.json()["detail"]

    # Тест удаления связи ингредиента админом
    @pytest.mark.asyncio
    async def test_delete_menu_item_ingredient_as_admin(self, admin_client):
        with patch('app.services.ingredients_service.delete_menu_item_ingredient', 
                  return_value={"detail": "Ингредиент удален из состава позиции меню"}):
            
            response = await admin_client.delete("/menu-item-ingredients/1/1")

            assert response.status_code == 204

    # Тест получения всех связей ингредиентов
    @pytest.mark.asyncio
    async def test_get_all_menu_item_ingredients(self, client, test_db):
        response = await client.get("/menu-item-ingredients/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)