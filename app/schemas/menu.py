from pydantic import BaseModel, HttpUrl
from typing import Optional, List

from app.models.menu_items import MenuCategory

class ImageOut(BaseModel):
    image_id: int
    item_id: int
    image_url: str

    model_config = {
        "from_attributes": True
    }
        
class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: MenuCategory
    is_available: Optional[bool] = True

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemUpdate(MenuItemBase):
    image_urls: Optional[List[HttpUrl]] = None 

class MenuItemOut(MenuItemBase):
    item_id: int
    images: list[ImageOut] = []

    model_config = {
        "from_attributes": True
    }
