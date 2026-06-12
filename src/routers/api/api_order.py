from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.redis import get_redis_client
from src.services import auth_service, order_service
from src.schemas.order import OrderCreate

router = APIRouter(prefix="/api/order")

@router.post("/checkout")
async def process_checkout(request: Request, body: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Xử lý đặt hàng bất đồng bộ bằng transaction và cập nhật dữ liệu tồn kho."""
    current_user = await auth_service.get_current_user(request, db)
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Vui lòng đăng nhập để thực hiện thanh toán")
    redis_client = await get_redis_client()
    cart_id = f"user_{current_user.id}"
    try:
        order = await order_service.create_order(
            db=db,
            redis_client=redis_client,
            cart_id=cart_id,
            user_id=current_user.id,
            shipping_address=body.shipping_address,
            recipient_name=body.recipient_name,
            recipient_phone=body.recipient_phone
        )
        return {"success": True, "order_id": order.id}
    except HTTPException as he:
        raise he
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
