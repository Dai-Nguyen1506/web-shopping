from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """Schema dữ liệu dùng để đăng ký tài khoản người dùng mới."""
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    """Schema dữ liệu dùng để đăng nhập hệ thống."""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema dữ liệu trả về thông tin người dùng."""
    id: int
    email: str
    full_name: str
    is_admin: bool

    class Config:
        from_attributes = True
