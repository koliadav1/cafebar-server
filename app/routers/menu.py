import asyncio
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.menu_items import MenuItem, MenuItemImage
from app.schemas import menu as schemas
from app.services import menu_service as service
from app.realtime.websocket_manager import manager
from app.services.auth_service import get_current_user
from app.services.yandex_storage import upload_image_to_yandex

router = APIRouter(
    prefix="/menu",
    tags=["Меню"]
)

# Получение всех позиций меню
@router.get("/", response_model=list[schemas.MenuItemOut])
async def read_all_menu_items(db: AsyncSession = Depends(get_db)) -> List[MenuItem]:
    return await service.get_all_menu_items(db)

# Получение позиции меню по id
@router.get("/{item_id}", response_model=schemas.MenuItemOut)
async def read_menu_item(item_id: int, db: AsyncSession = Depends(get_db)) -> MenuItem:
    item = await service.get_menu_item_by_id(item_id, db)
    return item

# Создание позиции меню
@router.post("/", response_model=schemas.MenuItemOut, status_code=201)
async def create_menu_item(item: schemas.MenuItemCreate, 
                           db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)) -> MenuItem:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут изменять меню")
    menu_item = await service.create_menu_item(item, db)
    await manager.broadcast({
        "type": "menu_create",
        "payload": {"action": "create", "item": schemas.MenuItemOut.model_validate(menu_item).model_dump()}
    })
    return menu_item

# Изменение позиции меню по id
@router.put("/{item_id}", response_model=schemas.MenuItemOut)
async def update_menu_item(item_id: int, 
                           item: schemas.MenuItemUpdate,
                           db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)) -> MenuItem:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут изменять меню")
    menu_item = await service.update_menu_item(item_id, item, db)
    await manager.broadcast({
        "type": "menu_update",
        "payload": {"action": "update", "item": schemas.MenuItemOut.model_validate(menu_item).model_dump()}
    })
    return menu_item

# Удаление позиции меню по id
@router.delete("/{item_id}")
async def delete_menu_item(item_id: int, 
                           db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)) -> dict[str, str]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут изменять меню")
    result = await service.delete_menu_item(item_id, db)
    await manager.broadcast({
        "type": "menu_delete",
        "payload": {"action": "delete", "item_id": item_id}
    })
    return result

# Добавить изображение к позиции меню
@router.post("/{item_id}/upload-image", response_model=schemas.ImageOut)
async def upload_menu_item_image(
                            item_id: int,
                            file: UploadFile = File(...),
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user)) -> MenuItemImage:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут изменять меню")

    print(f"[UPLOAD] Попытка загрузки изображения для item_id={item_id} пользователем {current_user.user_id}")

    result = await db.execute(select(MenuItem).where(MenuItem.item_id == item_id))
    menu_item = result.scalar_one_or_none()
    if not menu_item:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")
    
    try:
        image_url = upload_image_to_yandex(file.file, file.filename)
        print(f"[UPLOAD] Успешная загрузка изображения, URL: {image_url}")
    except Exception as e:
        print(f"[UPLOAD ERROR] Ошибка загрузки в облако: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки изображения: {str(e)}")

    try:
        new_image = MenuItemImage(item_id=item_id, image_url=image_url)
        db.add(new_image)
        await db.commit()
        await db.refresh(new_image)
        print(f"[UPLOAD] Изображение сохранено в БД с ID {new_image.image_id}")
        return new_image
    except Exception as e:
        await db.rollback()
        print(f"[DB ERROR] Ошибка при сохранении изображения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении изображения в БД: {str(e)}")