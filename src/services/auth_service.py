from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException, status
from src.config import settings
from src.repositories.user_repo import UserRepository
from src.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác thực xem mật khẩu thô có khớp với mật khẩu đã mã hóa hay không."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Mã hóa mật khẩu bằng thuật toán bcrypt."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT token truy cập chứa dữ liệu payload và thời gian hết hạn."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Xác thực thông tin đăng nhập của người dùng dựa trên email và mật khẩu."""
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if user and verify_password(password, user.hashed_password):
        return user
    return None

async def get_current_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """Giải mã token và trả về thông tin người dùng hiện tại từ cơ sở dữ liệu."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    repo = UserRepository(db)
    return await repo.get_by_email(email)

async def get_current_user(request: Request, db: AsyncSession) -> Optional[User]:
    """Lấy người dùng hiện tại từ cookie access_token hoặc header Authorization."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        return None
    return await get_current_user_from_token(token, db)
