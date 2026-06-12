from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.coupon import Coupon
from src.repositories.base import BaseRepository

class CouponRepository(BaseRepository[Coupon]):
    """Repository quản lý các truy vấn và thao tác trên bảng coupons."""

    def __init__(self, db: AsyncSession):
        """Khởi tạo CouponRepository với model Coupon."""
        super().__init__(Coupon, db)

    async def get_by_code(self, code: str) -> Optional[Coupon]:
        """Lấy thông tin mã giảm giá dựa trên mã code viết hoa."""
        result = await self.db.execute(select(Coupon).filter(Coupon.code == code.strip().upper()))
        return result.scalars().first()

    async def get_active_coupons(self) -> List[Coupon]:
        """Lấy danh sách tất cả các mã giảm giá đang hoạt động."""
        result = await self.db.execute(select(Coupon).filter(Coupon.is_active == True))
        return result.scalars().all()
