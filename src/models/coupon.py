from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from src.database import Base

class Coupon(Base):
    """Đại diện cho bảng mã giảm giá trong hệ thống."""
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(String, nullable=False)
    discount_value = Column(Float, nullable=False)
    min_order_value = Column(Float, default=0.0)
    max_discount_amount = Column(Float, nullable=True)
    usage_limit = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
