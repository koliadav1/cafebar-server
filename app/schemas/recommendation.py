from pydantic import BaseModel

from app.models.menu_items import MenuCategory

class RecommendedItem(BaseModel):
    item_id: int
    name: str
    category: MenuCategory
    order_count: int

    model_config = {
        "from_attributes": True
    }
