from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.order import Order, OrderItem
from src.repositories.base import BaseRepository

class OrderRepository(BaseRepository[Order]):
    """Repository quản lý các truy vấn và thao tác trên bảng orders."""

    def __init__(self, db: AsyncSession):
        """Khởi tạo OrderRepository với model Order."""
        super().__init__(Order, db)

    async def get_by_user_id(self, user_id: int) -> List[Order]:
        """Lấy tất cả các đơn hàng của một người dùng cụ thể."""
        result = await self.db.execute(
            select(Order)
            .filter(Order.user_id == user_id)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_order_details(self, order_id: int) -> Optional[Order]:
        """Lấy chi tiết một đơn hàng kèm theo các mặt hàng và coupon liên kết."""
        result = await self.db.execute(
            select(Order)
            .filter(Order.id == order_id)
            .options(selectinload(Order.items).selectinload(OrderItem.product), selectinload(Order.coupon))
        )
        return result.scalars().first()
