import json
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.product_repo import ProductRepository
from src.models.product import Product

async def add_to_cart(redis_client, cart_id: str, product_id: int, quantity: int = 1) -> int:
    """Thêm sản phẩm hoặc tăng số lượng sản phẩm trong giỏ hàng trên Redis."""
    return await redis_client.hincrby(f"cart:{cart_id}", str(product_id), quantity)

async def update_cart_item(redis_client, cart_id: str, product_id: int, quantity: int) -> int:
    """Cập nhật trực tiếp số lượng của một sản phẩm trong giỏ hàng trên Redis."""
    if quantity <= 0:
        await redis_client.hdel(f"cart:{cart_id}", str(product_id))
        return 0
    await redis_client.hset(f"cart:{cart_id}", str(product_id), quantity)
    return quantity

async def remove_from_cart(redis_client, cart_id: str, product_id: int) -> int:
    """Xóa hoàn toàn sản phẩm khỏi giỏ hàng trên Redis."""
    return await redis_client.hdel(f"cart:{cart_id}", str(product_id))

async def get_cart(redis_client, cart_id: str, db: AsyncSession) -> List[Dict]:
    """Lấy danh sách sản phẩm trong giỏ hàng kèm theo thông tin chi tiết từ database."""
    cart_data = await redis_client.hgetall(f"cart:{cart_id}")
    items = []
    repo = ProductRepository(db)
    for p_id_bytes, qty_bytes in cart_data.items():
        p_id = p_id_bytes.decode() if isinstance(p_id_bytes, bytes) else p_id_bytes
        qty = int(qty_bytes.decode() if isinstance(qty_bytes, bytes) else qty_bytes)
        product = await repo.get(int(p_id))
        if product:
            items.append({
                "product": product,
                "quantity": qty,
                "subtotal": product.price * qty
            })
    return items

async def apply_coupon(redis_client, cart_id: str, coupon_code: str) -> bool:
    """Lưu mã giảm giá đã áp dụng vào giỏ hàng trên Redis."""
    await redis_client.set(f"cart:{cart_id}:coupon", coupon_code.strip().upper())
    return True

async def get_applied_coupon(redis_client, cart_id: str) -> Optional[str]:
    """Lấy mã giảm giá đã áp dụng cho giỏ hàng hiện tại."""
    code = await redis_client.get(f"cart:{cart_id}:coupon")
    return code.decode() if isinstance(code, bytes) else code

async def remove_coupon(redis_client, cart_id: str) -> bool:
    """Xóa bỏ mã giảm giá đang áp dụng khỏi giỏ hàng."""
    await redis_client.delete(f"cart:{cart_id}:coupon")
    return True

async def merge_carts(redis_client, source_id: str, target_id: str) -> bool:
    """Đồng bộ và gộp giỏ hàng vãng lai vào giỏ hàng thành viên."""
    source_cart = await redis_client.hgetall(f"cart:{source_id}")
    for p_id_bytes, qty_bytes in source_cart.items():
        p_id = p_id_bytes.decode() if isinstance(p_id_bytes, bytes) else p_id_bytes
        qty = int(qty_bytes.decode() if isinstance(qty_bytes, bytes) else qty_bytes)
        await redis_client.hincrby(f"cart:{target_id}", p_id, qty)
    source_coupon = await get_applied_coupon(redis_client, source_id)
    if source_coupon:
        await apply_coupon(redis_client, target_id, source_coupon)
    await clear_cart(redis_client, source_id)
    return True

async def clear_cart(redis_client, cart_id: str) -> bool:
    """Xóa sạch giỏ hàng và mã giảm giá liên quan trên Redis."""
    await redis_client.delete(f"cart:{cart_id}")
    await redis_client.delete(f"cart:{cart_id}:coupon")
    return True
