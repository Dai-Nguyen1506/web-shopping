from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    """Schema dữ liệu dùng để tạo mới hoặc cập nhật thông tin sản phẩm."""
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    image_url: Optional[str] = None
    category: Optional[str] = None

class ProductResponse(BaseModel):
    """Schema dữ liệu trả về thông tin chi tiết của sản phẩm."""
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    image_url: Optional[str]
    category: Optional[str]

    class Config:
        from_attributes = True
