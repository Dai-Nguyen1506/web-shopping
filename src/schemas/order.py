from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.schemas.product import ProductResponse

class OrderItemResponse(BaseModel):
    """Schema dữ liệu trả về thông tin của một mặt hàng trong đơn hàng."""
    id: int
    product_id: int
    quantity: int
    price: float
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    """Schema dữ liệu khách hàng gửi lên khi đặt hàng."""
    shipping_address: str
    recipient_name: str
    recipient_phone: str

class OrderResponse(BaseModel):
    """Schema dữ liệu trả về thông tin chi tiết của đơn hàng."""
    id: int
    user_id: Optional[int]
    status: str
    total_amount: float
    discount_amount: float
    final_amount: float
    shipping_address: str
    recipient_name: str
    recipient_phone: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
