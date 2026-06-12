from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Repository cơ sở cung cấp các phương thức CRUD chuẩn."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """Khởi tạo với SQLAlchemy model và db session."""
        self.model = model
        self.db = db

    async def get(self, id: any) -> Optional[ModelType]:
        """Lấy một bản ghi theo khóa chính."""
        result = await self.db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Lấy danh sách tất cả các bản ghi có phân trang."""
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, obj: ModelType) -> ModelType:
        """Tạo một bản ghi mới trong database."""
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def delete(self, id: any) -> bool:
        """Xóa một bản ghi theo khóa chính."""
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
            return True
        return False
