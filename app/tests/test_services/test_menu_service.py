import pytest
from fastapi import HTTPException

from app.services.menu_service import (
    get_all_menu_items, 
    get_menu_item_by_id, 
    create_menu_item, 
    update_menu_item, 
    delete_menu_item
)
from app.schemas.menu import MenuItemCreate
from app.models.menu_items import MenuItem


class TestMenuService:
    # Тест получения всех позиций меню
    def test_get_all_menu_items_success(self, test_db, sample_menu_item):
        from app.models.menu_items import MenuItemImage

        image = MenuItemImage(
            item_id=sample_menu_item.item_id, 
            image_url="http://test.com/test.jpg"
        )
        test_db.add(image)
        test_db.commit()

        result = get_all_menu_items(test_db)

        assert len(result) >= 1
        menu_item_ids = [item.item_id for item in result]
        assert sample_menu_item.item_id in menu_item_ids

        test_item = next((item for item in result if item.item_id == sample_menu_item.item_id), None)
        assert test_item is not None
        assert test_item.name == sample_menu_item.name
        assert test_item.image_urls == ["http://test.com/test.jpg"]

    # Тест получения позиции меню по ID
    def test_get_menu_item_by_id_success(self, test_db, sample_menu_item):
        from app.models.menu_items import MenuItemImage

        image = MenuItemImage(
            item_id=sample_menu_item.item_id,
            image_url="http://test.com/image.jpg"
        )
        test_db.add(image)
        test_db.commit()

        result = get_menu_item_by_id(sample_menu_item.item_id, test_db)

        assert result.name == sample_menu_item.name
        assert result.price == sample_menu_item.price
        assert result.image_urls == ["http://test.com/image.jpg"]

    # Тест получения несуществующей позиции меню
    def test_get_menu_item_by_id_not_found(self, test_db):
        with pytest.raises(HTTPException) as exc_info:
            get_menu_item_by_id(999, test_db)
        assert exc_info.value.status_code == 404
        assert "Позиция меню не найдена" in str(exc_info.value.detail)

    # Тест создания позиции меню
    def test_create_menu_item_success(self, test_db, sample_menu_item_data):
        from app.models.menu_items import MenuCategory
        
        item_data_dict = sample_menu_item_data.copy()
        item_data_dict["category"] = MenuCategory(sample_menu_item_data["category"])
        
        from app.schemas.menu import MenuItemCreate
        item_data = MenuItemCreate(**item_data_dict)
        
        result = create_menu_item(item_data, test_db)
        
        assert result.name == "Тестовое блюдо"
        assert result.price == 300.00
        assert result.category == MenuCategory.MAIN
        assert result.is_available == True

    # Тест обновления позиции меню
    def test_update_menu_item_success(self, test_db, sample_menu_item_data):
        from app.models.menu_items import MenuCategory
        from app.schemas.menu import MenuItemCreate, MenuItemUpdate
        
        item_data_dict = sample_menu_item_data.copy()
        item_data_dict["category"] = MenuCategory(sample_menu_item_data["category"])
        item_data = MenuItemCreate(**item_data_dict)
        
        created_item = create_menu_item(item_data, test_db)

        update_data = MenuItemUpdate(
            name="Обновленное блюдо",
            price=350.00,
            category=MenuCategory.MAIN.value,
            is_available=False
        )
        
        result = update_menu_item(created_item.item_id, update_data, test_db)
        
        assert result.name == "Обновленное блюдо"
        assert result.price == 350.00
        assert result.is_available == False

    # Тест удаления позиции меню
    def test_delete_menu_item_success(self, test_db, sample_menu_item_data):
        item_data = MenuItemCreate(**sample_menu_item_data)
        created_item = create_menu_item(item_data, test_db)
        
        result = delete_menu_item(created_item.item_id, test_db)
        
        assert result == {"detail": "Позиция меню удалена"}
        
        db_item = test_db.query(MenuItem).filter(MenuItem.item_id == created_item.item_id).first()
        assert db_item is None