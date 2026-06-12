import os
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, responses, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services import auth_service, cart_service, coupon_service
from src.redis import get_redis_client
from src.repositories.order_repo import OrderRepository
from fastapi.templating import Jinja2Templates

router = APIRouter()
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/cart")
async def get_cart_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Hiển thị trang giỏ hàng chi tiết cùng thông tin mã giảm giá đã áp dụng."""
    current_user = await auth_service.get_current_user(request, db)
    redis_client = await get_redis_client()
    session_id = request.cookies.get("session_id")
    print("GET /cart - request session_id cookie:", session_id)
    response_cookie = None
    if not current_user and not session_id:
        session_id = str(uuid.uuid4())
        response_cookie = session_id
    cart_id = f"user_{current_user.id}" if current_user else f"anon_{session_id}"
    print("GET /cart - cart_id:", cart_id)
    cart_items = await cart_service.get_cart(redis_client, cart_id, db)
    coupon_code = await cart_service.get_applied_coupon(redis_client, cart_id)
    coupon_info = None
    discount_amount = 0.0
    total_amount = sum(item["subtotal"] for item in cart_items)
    if coupon_code:
        val_res = await coupon_service.validate_coupon(db, redis_client, coupon_code, total_amount)
        if val_res["valid"]:
            coupon_info = val_res["coupon"]
            discount_amount = coupon_service.calculate_discount(coupon_info, total_amount)
        else:
            await cart_service.remove_coupon(redis_client, cart_id)
    response = templates.TemplateResponse(
        request=request,
        name="cart/index.html",
        context={
            "request": request,
            "cart_items": cart_items,
            "total_amount": total_amount,
            "discount_amount": discount_amount,
            "final_amount": total_amount - discount_amount,
            "coupon_code": coupon_code or "",
            "coupon_info": coupon_info,
            "current_user": current_user
        }
    )
    if response_cookie:
        response.set_cookie(key="session_id", value=response_cookie, httponly=True)
    return response

@router.get("/checkout")
async def get_checkout_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Hiển thị trang điền thông tin thanh toán cho đơn hàng."""
    current_user = await auth_service.get_current_user(request, db)
    if not current_user:
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redis_client = await get_redis_client()
    cart_id = f"user_{current_user.id}"
    cart_items = await cart_service.get_cart(redis_client, cart_id, db)
    if not cart_items:
        return responses.RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)
    total_amount = sum(item["subtotal"] for item in cart_items)
    coupon_code = await cart_service.get_applied_coupon(redis_client, cart_id)
    coupon_info = None
    discount_amount = 0.0
    if coupon_code:
        val_res = await coupon_service.validate_coupon(db, redis_client, coupon_code, total_amount)
        if val_res["valid"]:
            coupon_info = val_res["coupon"]
            discount_amount = coupon_service.calculate_discount(coupon_info, total_amount)
    response = templates.TemplateResponse(
        request=request,
        name="checkout/index.html",
        context={
            "request": request,
            "cart_items": cart_items,
            "total_amount": total_amount,
            "discount_amount": discount_amount,
            "final_amount": total_amount - discount_amount,
            "coupon_code": coupon_code or "",
            "coupon_info": coupon_info,
            "current_user": current_user
        }
    )
    return response

@router.get("/checkout/success/{order_id}")
async def get_checkout_success_page(request: Request, order_id: int, db: AsyncSession = Depends(get_db)):
    """Hiển thị thông tin hóa đơn khi khách hàng đặt hàng thành công."""
    current_user = await auth_service.get_current_user(request, db)
    repo = OrderRepository(db)
    order = await repo.get_order_details(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return templates.TemplateResponse(
        request=request,
        name="checkout/success.html",
        context={
            "request": request,
            "order": order,
            "current_user": current_user
        }
    )
