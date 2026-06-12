from sqlalchemy import Column, Integer, String, Float
from src.database import Base

class Product(Base):
    """Đại diện cho bảng sản phẩm trong hệ thống."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image_url = Column(String, nullable=True)
    category = Column(String, index=True, nullable=True)
