import os
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Form, responses, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services import auth_service, coupon_service
from src.repositories.coupon_repo import CouponRepository
from src.repositories.product_repo import ProductRepository
from src.models.coupon import Coupon
from src.models.product import Product
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin")
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

async def require_admin(request: Request, db: AsyncSession = Depends(get_db)) -> bool:
    """Kiểm tra và chỉ cho phép người dùng có quyền quản trị truy cập."""
    current_user = await auth_service.get_current_user(request, db)
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền truy cập")
    return True

@router.get("/dashboard")
async def get_admin_dashboard(request: Request, db: AsyncSession = Depends(get_db), authenticated: bool = Depends(require_admin)):
    """Hiển thị bảng điều khiển admin quản lý sản phẩm và mã giảm giá."""
    current_user = await auth_service.get_current_user(request, db)
    coupon_repo = CouponRepository(db)
    product_repo = ProductRepository(db)
    coupons = await coupon_repo.get_all()
    products = await product_repo.get_all()
    return templates.TemplateResponse(
        request=request,
        name="admin/coupons.html",
        context={
            "request": request,
            "coupons": coupons,
            "products": products,
            "current_user": current_user
        }
    )

@router.post("/coupon/create")
async def create_coupon(
    request: Request,
    code: str = Form(...),
    discount_type: str = Form(...),
    discount_value: float = Form(...),
    min_order_value: float = Form(0.0),
    max_discount_amount: float = Form(None),
    usage_limit: int = Form(1),
    start_date: str = Form(None),
    end_date: str = Form(None),
    db: AsyncSession = Depends(get_db),
    authenticated: bool = Depends(require_admin)
):
    """Tạo mới mã giảm giá với các điều kiện ràng buộc cụ thể."""
    repo = CouponRepository(db)
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    coupon = Coupon(
        code=code.strip().upper(),
        discount_type=discount_type,
        discount_value=discount_value,
        min_order_value=min_order_value,
        max_discount_amount=max_discount_amount,
        usage_limit=usage_limit,
        start_date=start_dt,
        end_date=end_dt,
        is_active=True
    )
    await repo.create(coupon)
    return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/coupon/toggle/{coupon_id}")
async def toggle_coupon(
    coupon_id: int,
    db: AsyncSession = Depends(get_db),
    authenticated: bool = Depends(require_admin)
):
    """Bật hoặc tắt trạng thái kích hoạt của mã giảm giá."""
    repo = CouponRepository(db)
    coupon = await repo.get(coupon_id)
    if coupon:
        coupon.is_active = not coupon.is_active
    return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/coupon/delete/{coupon_id}")
async def delete_coupon(
    coupon_id: int,
    db: AsyncSession = Depends(get_db),
    authenticated: bool = Depends(require_admin)
):
    """Thực hiện vô hiệu hóa (soft delete) mã giảm giá để bảo toàn dữ liệu cũ."""
    repo = CouponRepository(db)
    coupon = await repo.get(coupon_id)
    if coupon:
        coupon.is_active = False
    return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/product/create")
async def create_product(
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    stock: int = Form(0),
    image_url: str = Form(None),
    category: str = Form(None),
    db: AsyncSession = Depends(get_db),
    authenticated: bool = Depends(require_admin)
):
    """Tạo mới một sản phẩm trong hệ thống quản trị cửa hàng."""
    repo = ProductRepository(db)
    prod = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        image_url=image_url,
        category=category
    )
    await repo.create(prod)
    return responses.RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
