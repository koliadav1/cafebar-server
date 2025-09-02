from sqlalchemy import Column, ForeignKey, Integer, String, Text, Numeric, Boolean
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base

class MenuItemImage(Base):
    __tablename__ = "menu_item_images"

    image_id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("menu_items.item_id", ondelete="CASCADE"))
    image_url = Column(String)

class MenuCategory(str, Enum):
    MAIN = "Main_course"
    GARNISH = "Garnish"
    STARTER = "Starter"
    SOUP = "Soup"
    SNACK = "Snack"
    DRINK = "Drink"
    DESSERT = "Dessert"
    OTHER = "Other"

class MenuItem(Base):
    __tablename__ = "menu_items"

    item_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    price = Column(Numeric)
    category = Column(SQLEnum(MenuCategory), nullable=False)
    is_available = Column(Boolean, default=True)

    images = relationship("MenuItemImage", backref="menu_item", cascade="all, delete")