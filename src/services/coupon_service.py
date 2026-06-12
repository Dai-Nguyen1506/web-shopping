import json
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.coupon_repo import CouponRepository
from src.models.coupon import Coupon

async def cache_coupon(redis_client, coupon: Coupon):
    """Lưu trữ cấu hình mã giảm giá lên bộ đệm Redis để truy xuất nhanh."""
    data = {
        "id": coupon.id,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "min_order_value": coupon.min_order_value,
        "max_discount_amount": coupon.max_discount_amount,
        "usage_limit": coupon.usage_limit,
        "used_count": coupon.used_count,
        "start_date": coupon.start_date.isoformat() if coupon.start_date else None,
        "end_date": coupon.end_date.isoformat() if coupon.end_date else None,
        "is_active": coupon.is_active
    }
    await redis_client.set(f"coupon:info:{coupon.code}", json.dumps(data), ex=300)

async def get_coupon_info(db: AsyncSession, redis_client, code: str) -> Optional[Dict]:
    """Lấy thông tin mã giảm giá từ bộ đệm Redis hoặc truy vấn database nếu chưa có."""
    code_upper = code.strip().upper()
    cached = await redis_client.get(f"coupon:info:{code_upper}")
    if cached:
        return json.loads(cached)
    repo = CouponRepository(db)
    coupon = await repo.get_by_code(code_upper)
    if coupon:
        await cache_coupon(redis_client, coupon)
        return {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "min_order_value": coupon.min_order_value,
            "max_discount_amount": coupon.max_discount_amount,
            "usage_limit": coupon.usage_limit,
            "used_count": coupon.used_count,
            "start_date": coupon.start_date.isoformat() if coupon.start_date else None,
            "end_date": coupon.end_date.isoformat() if coupon.end_date else None,
            "is_active": coupon.is_active
        }
    return None

async def validate_coupon(db: AsyncSession, redis_client, code: str, total_amount: float) -> Dict:
    """Kiểm tra tính hợp lệ toàn diện của mã giảm giá cho đơn hàng."""
    info = await get_coupon_info(db, redis_client, code)
    if not info or not info["is_active"]:
        return {"valid": False, "message": "Mã giảm giá không tồn tại hoặc đã bị vô hiệu hóa"}
    now = datetime.now()
    if info["start_date"]:
        start = datetime.fromisoformat(info["start_date"])
        if now < start:
            return {"valid": False, "message": "Mã giảm giá chưa đến thời gian áp dụng"}
    if info["end_date"]:
        end = datetime.fromisoformat(info["end_date"])
        if now > end:
            return {"valid": False, "message": "Mã giảm giá đã hết hạn sử dụng"}
    if info["used_count"] >= info["usage_limit"]:
        return {"valid": False, "message": "Mã giảm giá đã hết lượt sử dụng"}
    if total_amount < info["min_order_value"]:
        return {"valid": False, "message": f"Giá trị đơn hàng chưa đạt mức tối thiểu {info['min_order_value']:,}đ"}
    return {"valid": True, "coupon": info}

def calculate_discount(coupon_info: Dict, total_amount: float) -> float:
    """Tính toán số tiền giảm giá dựa trên loại mã giảm giá và tổng tiền đơn hàng."""
    if coupon_info["discount_type"] == "percentage":
        discount = total_amount * (coupon_info["discount_value"] / 100.0)
        if coupon_info["max_discount_amount"] is not None:
            discount = min(discount, coupon_info["max_discount_amount"])
    else:
        discount = coupon_info["discount_value"]
    return min(discount, total_amount)
