from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReviewBase(BaseModel):
    user_id: int
    order_id: int
    rating: int
    comment: Optional[str] = None
    admin_response: Optional[str] = None

class ReviewCreate(BaseModel):
    order_id: int
    rating: int
    comment: Optional[str] = None

class ReviewUpdate(ReviewCreate):
    pass

class ReviewInDB(ReviewBase):
    review_id: int
    review_date: datetime

    model_config = {
        "from_attributes": True
    }

class Review(ReviewInDB):
    pass

class AdminReviewResponse(BaseModel):
    admin_response: str

