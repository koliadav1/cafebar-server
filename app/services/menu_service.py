from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.menu_items import MenuItem, MenuItemImage
from app.schemas import menu as schemas

#Получить меню
def get_all_menu_items(db: Session) -> List[MenuItem]:
    items = db.query(MenuItem).all()
    for item in items:
        item.image_urls = [img.image_url for img in item.images]
    return items

#Получить позицию меню по id
def get_menu_item_by_id(item_id: int, db: Session) -> MenuItem:
    item = db.query(MenuItem).filter(MenuItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция меню не найдена")
    item.image_urls = [img.image_url for img in item.images]
    return item

#Создание позиции меню
def create_menu_item(item_data: schemas.MenuItemCreate, db: Session) -> MenuItem:
    item_dict = item_data.model_dump()
    new_item = MenuItem(**item_dict)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

#Изменение позиции меню
def update_menu_item(item_id: int, item_data: schemas.MenuItemUpdate, db: Session) -> MenuItem:
    item = get_menu_item_by_id(item_id, db)
    data = item_data.model_dump(exclude_unset=True, exclude={"image_urls"})

    for key, value in data.items():
        setattr(item, key, value)

    if item_data.image_urls is not None:
        db.query(MenuItemImage).filter(MenuItemImage.item_id == item_id).delete()
        for url in item_data.image_urls:
            image_url_str = str(url)
            db.add(MenuItemImage(item_id=item_id, image_url=image_url_str))
    
    db.commit()
    db.refresh(item)
    item.image_urls = [img.image_url for img in item.images]
    return item

#Удаление позиции меню
def delete_menu_item(item_id: int, db: Session):
    item = get_menu_item_by_id(item_id, db)
    db.delete(item)
    db.commit()
    return {"detail": "Позиция меню удалена"}

#Добавление изображения к позиции меню
def add_item_image(db: Session, item_id: int, image_url: str) -> MenuItemImage:
    image = MenuItemImage(item_id=item_id, image_url=image_url)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image