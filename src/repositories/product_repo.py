from typing import List
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product
from src.repositories.base import BaseRepository

class ProductRepository(BaseRepository[Product]):
    """Repository quản lý các truy vấn và thao tác trên bảng products."""

    def __init__(self, db: AsyncSession):
        """Khởi tạo ProductRepository với model Product."""
        super().__init__(Product, db)

    async def search_and_filter(
        self,
        query: str = None,
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Tìm kiếm và lọc sản phẩm theo các tiêu chí khác nhau."""
        stmt = select(Product)
        if query:
            stmt = stmt.filter(Product.name.icontains(query) | Product.description.icontains(query))
        if category:
            stmt = stmt.filter(Product.category == category)
        if min_price is not None:
            stmt = stmt.filter(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.filter(Product.price <= max_price)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_categories(self) -> List[str]:
        """Lấy danh sách tất cả các danh mục sản phẩm duy nhất."""
        result = await self.db.execute(select(distinct(Product.category)))
        return [c for c in result.scalars().all() if c is not None]
