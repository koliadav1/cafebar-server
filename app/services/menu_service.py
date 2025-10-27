from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models.menu_items import MenuItem, MenuItemImage
from app.schemas import menu as schemas

# Получить меню
async def get_all_menu_items(db: AsyncSession) -> List[MenuItem]:
    result = await db.execute(
        select(MenuItem).options(selectinload(MenuItem.images))
    )
    items = result.scalars().all()
    for item in items:
        item.image_urls = [img.image_url for img in item.images]
    return items

# Получить позицию меню по id
async def get_menu_item_by_id(item_id: int, db: AsyncSession) -> MenuItem:
    result = await db.execute(
        select(MenuItem)
        .where(MenuItem.item_id == item_id)
        .options(selectinload(MenuItem.images))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Позиция меню не найдена")
    item.image_urls = [img.image_url for img in item.images]
    return item

# Создание позиции меню
async def create_menu_item(item_data: schemas.MenuItemCreate, db: AsyncSession) -> MenuItem:
    item_dict = item_data.model_dump()
    new_item = MenuItem(**item_dict)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

# Изменение позиции меню
async def update_menu_item(item_id: int, item_data: schemas.MenuItemUpdate, db: AsyncSession) -> MenuItem:
    item = await get_menu_item_by_id(item_id, db)
    data = item_data.model_dump(exclude_unset=True, exclude={"image_urls"})

    for key, value in data.items():
        setattr(item, key, value)

    if item_data.image_urls is not None:
        await db.execute(
            delete(MenuItemImage).where(MenuItemImage.item_id == item_id)
        )
        for url in item_data.image_urls:
            image_url_str = str(url)
            db.add(MenuItemImage(item_id=item_id, image_url=image_url_str))
    
    await db.commit()
    await db.refresh(item)

    item = await get_menu_item_by_id(item_id, db)
    item.image_urls = [img.image_url for img in item.images]
    return item

# Удаление позиции меню
async def delete_menu_item(item_id: int, db: AsyncSession):
    item = await get_menu_item_by_id(item_id, db)
    await db.delete(item)
    await db.commit()
    return {"detail": "Позиция меню удалена"}

# Добавление изображения к позиции меню
async def add_item_image(db: AsyncSession, item_id: int, image_url: str) -> MenuItemImage:
    image = MenuItemImage(item_id=item_id, image_url=image_url)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image