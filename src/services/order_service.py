from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from src.models.order import Order, OrderItem
from src.models.product import Product
from src.models.coupon import Coupon
from src.services import cart_service, coupon_service

async def create_order(
    db: AsyncSession,
    redis_client,
    cart_id: str,
    user_id: int,
    shipping_address: str,
    recipient_name: str,
    recipient_phone: str
) -> Order:
    """Tạo đơn hàng mới sử dụng transaction bất đồng bộ, cập nhật tồn kho và áp dụng mã giảm giá."""
    cart_items = await cart_service.get_cart(redis_client, cart_id, db)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Giỏ hàng trống")
    total_amount = sum(item["subtotal"] for item in cart_items)
    coupon_code = await cart_service.get_applied_coupon(redis_client, cart_id)
    coupon_obj = None
    discount_amount = 0.0
    if coupon_code:
        coupon_res = await db.execute(
            select(Coupon).filter(Coupon.code == coupon_code).with_for_update()
        )
        coupon_obj = coupon_res.scalars().first()
        if not coupon_obj or not coupon_obj.is_active or coupon_obj.used_count >= coupon_obj.usage_limit:
            raise HTTPException(status_code=400, detail="Mã giảm giá không còn hiệu lực")
        if total_amount < coupon_obj.min_order_value:
            raise HTTPException(status_code=400, detail="Đơn hàng không đủ điều kiện tối thiểu áp dụng mã")
        coupon_dict = {
            "discount_type": coupon_obj.discount_type,
            "discount_value": coupon_obj.discount_value,
            "max_discount_amount": coupon_obj.max_discount_amount
        }
        discount_amount = coupon_service.calculate_discount(coupon_dict, total_amount)
        coupon_obj.used_count += 1
    final_amount = total_amount - discount_amount
    order = Order(
        user_id=user_id,
        status="pending",
        total_amount=total_amount,
        coupon_id=coupon_obj.id if coupon_obj else None,
        discount_amount=discount_amount,
        final_amount=final_amount,
        shipping_address=shipping_address,
        recipient_name=recipient_name,
        recipient_phone=recipient_phone
    )
    db.add(order)
    await db.flush()
    for item in cart_items:
        prod_id = item["product"].id
        qty = item["quantity"]
        p_res = await db.execute(
            select(Product).filter(Product.id == prod_id).with_for_update()
        )
        db_product = p_res.scalars().first()
        if not db_product or db_product.stock < qty:
            raise HTTPException(status_code=400, detail=f"Sản phẩm {item['product'].name} không đủ hàng tồn kho")
        db_product.stock -= qty
        order_item = OrderItem(
            order_id=order.id,
            product_id=prod_id,
            quantity=qty,
            price=item["product"].price
        )
        db.add(order_item)
    await cart_service.clear_cart(redis_client, cart_id)
    await db.flush()
    return order
