import pytest
from unittest.mock import patch

from app.models.menu_items import MenuItem


class TestMenuRouter:
    # Тест получения всех позиций меню через API
    @pytest.mark.asyncio
    async def test_get_all_menu_items_success(self, client, test_db):
        from app.models.menu_items import MenuCategory
        
        item = MenuItem(name="Тестовое блюдо", price=150.0, category=MenuCategory.MAIN)
        test_db.add(item)
        await test_db.commit()

        response = await client.get("/menu/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Тестовое блюдо"
        assert data[0]["price"] == 150.0

    # Тест получения позиции меню по ID через API
    @pytest.mark.asyncio
    async def test_get_menu_item_by_id_success(self, client, test_db):
        from app.models.menu_items import MenuCategory
        
        item = MenuItem(name="Тестовое блюдо", price=150.0, category=MenuCategory.MAIN)
        test_db.add(item)
        await test_db.commit()

        response = await client.get(f"/menu/{item.item_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Тестовое блюдо"
        assert data["item_id"] == item.item_id

    # Тест получения несуществующей позиции меню через API
    @pytest.mark.asyncio
    async def test_get_menu_item_by_id_not_found(self, client):
        response = await client.get("/menu/999")
        
        assert response.status_code == 404
        assert "Позиция меню не найдена" in response.json()["detail"]

    # Тест создания позиции меню с правами админа
    @pytest.mark.asyncio
    async def test_create_menu_item_as_admin(self, admin_client, sample_menu_item_data, sample_menu_item, mock_websocket_manager):
        with patch('app.routers.menu.manager.broadcast', mock_websocket_manager.broadcast), \
            patch('app.services.menu_service.create_menu_item', return_value=sample_menu_item):
            
            response = await admin_client.post("/menu/", json=sample_menu_item_data)
            assert response.status_code == 201
            mock_websocket_manager.broadcast.assert_called_once()

    # Тест создания позиции меню без прав админа
    @pytest.mark.asyncio
    async def test_create_menu_item_as_non_admin(self, authenticated_client, sample_menu_item_data):
        response = await authenticated_client.post("/menu/", json=sample_menu_item_data)
        
        assert response.status_code == 403
        assert "Только админы могут изменять меню" in response.json()["detail"]

    # Тест обновления позиции меню
    @pytest.mark.asyncio
    async def test_update_menu_item_success(self, admin_client, sample_menu_item, mock_websocket_manager):
        sample_menu_item.name = "Обновленное блюдо"
        sample_menu_item.description = "Новое описание" 
        sample_menu_item.price = 350.00
        sample_menu_item.is_available = False

        update_data = {
            "name": "Обновленное блюдо",
            "description": "Новое описание",
            "price": 350.00,
            "category": sample_menu_item.category.value,
            "is_available": False
        }

        with patch('app.routers.menu.manager.broadcast', mock_websocket_manager.broadcast), \
            patch('app.services.menu_service.update_menu_item', return_value=sample_menu_item):
            
            response = await admin_client.put(f"/menu/{sample_menu_item.item_id}", json=update_data)
            
            assert response.status_code == 200
            mock_websocket_manager.broadcast.assert_called()

    # Тест удаления позиции меню
    @pytest.mark.asyncio
    async def test_delete_menu_item_success(self, admin_client, mock_websocket_manager):
        with patch('app.routers.menu.manager.broadcast', mock_websocket_manager.broadcast), \
            patch('app.services.menu_service.delete_menu_item', return_value={"detail": "позиция удалена"}):
            
            response = await admin_client.delete("/menu/1")
            
            assert response.status_code == 200
            assert response.json()["detail"] == "позиция удалена"
            mock_websocket_manager.broadcast.assert_called()