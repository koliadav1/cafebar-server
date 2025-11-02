import time
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
from app.dependencies.cache import get_cache_manager, CacheManager

router = APIRouter(
    prefix="/menu",
    tags=["Меню"]
)

# Получение всех позиций меню
@router.get("/", response_model=list[schemas.MenuItemOut])
async def read_all_menu_items(
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager)
) -> List[MenuItem]:
    start_time = time.time()
    cached_menu = await cache.get_cached("menu:all:active")
    if cached_menu:
        print(f"[REDIS] Menu from cache - {time.time() - start_time:.3f}s")
        return cached_menu
    
    menu_items = await service.get_all_menu_items(db)
    db_time = time.time() - start_time
    print(f"[REDIS] Menu from database - {db_time:.3f}s")
    
    menu_items_out = [schemas.MenuItemOut.model_validate(item) for item in menu_items]

    await cache.set_cached("menu:all:active", [item.model_dump() for item in menu_items_out], ttl=1800)
    
    return menu_items_out

# Получение позиции меню по id
@router.get("/{item_id}", response_model=schemas.MenuItemOut)
async def read_menu_item(
    item_id: int, 
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager)
) -> MenuItem:
    start_time = time.time()
    cache_key = f"menu:item:{item_id}"
    cached_item = await cache.get_cached(cache_key)
    if cached_item:
        print(f"[REDIS] Menu item from cache - {time.time() - start_time:.3f}s")
        return cached_item
    
    item = await service.get_menu_item_by_id(item_id, db)
    db_time = time.time() - start_time
    print(f"[REDIS] Menu item from database - {db_time:.3f}s")

    item_out = schemas.MenuItemOut.model_validate(item)
    await cache.set_cached(cache_key, item_out.model_dump(), ttl=3600)
    
    return item_out

# Создание позиции меню
@router.post("/", response_model=schemas.MenuItemOut, status_code=201)
async def create_menu_item(
    item: schemas.MenuItemCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cache: CacheManager = Depends(get_cache_manager)
) -> MenuItem:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут изменять меню")
    menu_item = await service.create_menu_item(item, db)
    
    await cache.invalidate_pattern("menu:all:*")
    await cache.invalidate_pattern("recommendations:*")
    
    await manager.broadcast({
        "type": "menu_create",
        "payload": {"action": "create", "item": schemas.MenuItemOut.model_validate(menu_item).model_dump()}
    })
    return menu_item

# Изменение позиции меню по id
@router.put("/{item_id}", response_model=schemas.MenuItemOut)
async def update_menu_item(
    item_id: int, 
    item: schemas.MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cache: CacheManager = Depends(get_cache_manager)
) -> MenuItem:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут изменять меню")
    menu_item = await service.update_menu_item(item_id, item, db)
    
    await cache.redis.delete(f"menu:item:{item_id}")
    await cache.invalidate_pattern("menu:all:*")
    await cache.invalidate_pattern("recommendations:*")
    
    await manager.broadcast({
        "type": "menu_update",
        "payload": {"action": "update", "item": schemas.MenuItemOut.model_validate(menu_item).model_dump()}
    })
    return menu_item

# Удаление позиции меню по id
@router.delete("/{item_id}")
async def delete_menu_item(
    item_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cache: CacheManager = Depends(get_cache_manager)
) -> dict[str, str]:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Только админы могут изменять меню")
    result = await service.delete_menu_item(item_id, db)
    
    await cache.redis.delete(f"menu:item:{item_id}")
    await cache.invalidate_pattern("menu:all:*")
    await cache.invalidate_pattern("recommendations:*")
    
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
    current_user: User = Depends(get_current_user),
    cache: CacheManager = Depends(get_cache_manager)
) -> MenuItemImage:
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
        
        await cache.redis.delete(f"menu:item:{item_id}")
        await cache.invalidate_pattern("menu:all:*")
        
        return new_image
    except Exception as e:
        await db.rollback()
        print(f"[DB ERROR] Ошибка при сохранении изображения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении изображения в БД: {str(e)}")