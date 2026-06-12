from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CouponCreate(BaseModel):
    """Schema dữ liệu dùng để tạo mới một mã giảm giá."""
    code: str
    discount_type: str
    discount_value: float
    min_order_value: Optional[float] = 0.0
    max_discount_amount: Optional[float] = None
    usage_limit: Optional[int] = 1
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = True

class CouponResponse(BaseModel):
    """Schema dữ liệu trả về thông tin của mã giảm giá."""
    id: int
    code: str
    discount_type: str
    discount_value: float
    min_order_value: float
    max_discount_amount: Optional[float]
    usage_limit: int
    used_count: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True
