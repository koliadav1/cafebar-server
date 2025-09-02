from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship

from app.database import Base

class Ingredient(Base):
    __tablename__ = "ingredients"

    ingredient_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    quantity = Column(Numeric, nullable=False)
    threshold = Column(Numeric, nullable=False)

    supply_orders = relationship('SupplyOrder', back_populates='ingredient')