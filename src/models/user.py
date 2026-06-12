from sqlalchemy import Column, Integer, String, Boolean
from src.database import Base

class User(Base):
    """Đại diện cho bảng người dùng trong hệ thống."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
