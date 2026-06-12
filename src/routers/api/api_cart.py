import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, responses, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.database import get_db
from src.redis import get_redis_client
from src.services import auth_service, cart_service, coupon_service

router = APIRouter(prefix="/api/cart")

class AddItemSchema(BaseModel):
    """Schema dữ liệu yêu cầu thêm sản phẩm vào giỏ hàng."""
    product_id: int
    quantity: int = 1

class UpdateItemSchema(BaseModel):
    """Schema dữ liệu yêu cầu cập nhật số lượng sản phẩm."""
    product_id: int
    quantity: int

class ApplyCouponSchema(BaseModel):
    """Schema dữ liệu yêu cầu áp dụng mã giảm giá."""
    code: str

@router.post("/add")
async def add_item(request: Request, body: AddItemSchema, db: AsyncSession = Depends(get_db)):
    """Thêm sản phẩm vào giỏ hàng trên Redis và cập nhật trạng thái session."""
    current_user = await auth_service.get_current_user(request, db)
    redis_client = await get_redis_client()
    session_id = request.cookies.get("session_id")
    response_cookie = None
    if not current_user and not session_id:
        session_id = str(uuid.uuid4())
        response_cookie = session_id
    cart_id = f"user_{current_user.id}" if current_user else f"anon_{session_id}"
    new_qty = await cart_service.add_to_cart(redis_client, cart_id, body.product_id, body.quantity)
    resp = responses.JSONResponse(content={"success": True, "new_quantity": new_qty})
    if response_cookie:
        resp.set_cookie(key="session_id", value=response_cookie, httponly=True)
    return resp

@router.post("/update")
async def update_item(request: Request, body: UpdateItemSchema, db: AsyncSession = Depends(get_db)):
    """Cập nhật trực tiếp số lượng của một mặt hàng trong giỏ hàng."""
    current_user = await auth_service.get_current_user(request, db)
    redis_client = await get_redis_client()
    session_id = request.cookies.get("session_id")
    cart_id = f"user_{current_user.id}" if current_user else f"anon_{session_id}"
    new_qty = await cart_service.update_cart_item(redis_client, cart_id, body.product_id, body.quantity)
    return {"success": True, "new_quantity": new_qty}

@router.post("/remove")
async def remove_item(request: Request, body: AddItemSchema, db: AsyncSession = Depends(get_db)):
    """Xóa hoàn toàn sản phẩm được chỉ định ra khỏi giỏ hàng."""
    current_user = await auth_service.get_current_user(request, db)
    redis_client = await get_redis_client()
    session_id = request.cookies.get("session_id")
    cart_id = f"user_{current_user.id}" if current_user else f"anon_{session_id}"
    await cart_service.remove_from_cart(redis_client, cart_id, body.product_id)
    return {"success": True}

@router.post("/apply-coupon")
async def apply_coupon(request: Request, body: ApplyCouponSchema, db: AsyncSession = Depends(get_db)):
    """Áp dụng mã giảm giá và tính toán số tiền được giảm thực tế."""
    current_user = await auth_service.get_current_user(request, db)
    redis_client = await get_redis_client()
    session_id = request.cookies.get("session_id")
    cart_id = f"user_{current_user.id}" if current_user else f"anon_{session_id}"
    cart_items = await cart_service.get_cart(redis_client, cart_id, db)
    total_amount = sum(item["subtotal"] for item in cart_items)
    val_res = await coupon_service.validate_coupon(db, redis_client, body.code, total_amount)
    if not val_res["valid"]:
        raise HTTPException(status_code=400, detail=val_res["message"])
    await cart_service.apply_coupon(redis_client, cart_id, body.code)
    discount = coupon_service.calculate_discount(val_res["coupon"], total_amount)
    return {
        "success": True,
        "coupon_code": body.code.upper(),
        "discount_amount": discount,
        "final_amount": total_amount - discount
    }

@router.post("/remove-coupon")
async def remove_coupon(request: Request, db: AsyncSession = Depends(get_db)):
    """Hủy bỏ việc áp dụng mã giảm giá hiện tại khỏi giỏ hàng."""
    current_user = await auth_service.get_current_user(request, db)
    redis_client = await get_redis_client()
    session_id = request.cookies.get("session_id")
    cart_id = f"user_{current_user.id}" if current_user else f"anon_{session_id}"
    await cart_service.remove_coupon(redis_client, cart_id)
    cart_items = await cart_service.get_cart(redis_client, cart_id, db)
    total_amount = sum(item["subtotal"] for item in cart_items)
    return {
        "success": True,
        "final_amount": total_amount
    }
