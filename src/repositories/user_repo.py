from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository quản lý các truy vấn và thao tác trên bảng users."""

    def __init__(self, db: AsyncSession):
        """Khởi tạo UserRepository với model User."""
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Lấy thông tin người dùng dựa trên địa chỉ email."""
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
