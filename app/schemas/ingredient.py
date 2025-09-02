from pydantic import BaseModel
from decimal import Decimal

class IngredientCreate(BaseModel):
    name: str
    unit: str
    quantity: Decimal
    threshold: Decimal
    
class IngredientOut(BaseModel):
    ingredient_id: int
    name: str
    unit: str

    model_config = {
        "from_attributes": True
    }

class MenuItemIngredientOut(BaseModel):
    item_id: int
    ingredient: IngredientOut
    required_quantity: Decimal

    model_config = {
        "from_attributes": True
    }

class MenuItemIngredientCreate(BaseModel):
    ingredient: IngredientCreate  # Включаем данные для создания нового ингредиента
    required_quantity: Decimal  # Необходимое количество
    
    model_config = {
        "from_attributes": True
    }