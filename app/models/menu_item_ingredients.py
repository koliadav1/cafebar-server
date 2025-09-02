from sqlalchemy import Column, Integer, Numeric
from sqlalchemy import ForeignKey

from app.database import Base

class MenuItemIngredient(Base):
    __tablename__ = "menu_item_ingredients"

    item_id = Column(Integer, ForeignKey('menu_items.item_id'), primary_key=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.ingredient_id'), primary_key=True, nullable=False)
    required_quantity = Column(Numeric, nullable=False)