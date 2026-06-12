import os
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.repositories.product_repo import ProductRepository
from src.services import auth_service
from fastapi.templating import Jinja2Templates

router = APIRouter()
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/")
async def get_shop_index(
    request: Request,
    q: str = None,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    db: AsyncSession = Depends(get_db)
):
    """Hiển thị trang chủ cửa hàng với các bộ lọc tìm kiếm và danh mục sản phẩm."""
    current_user = await auth_service.get_current_user(request, db)
    repo = ProductRepository(db)
    products = await repo.search_and_filter(
        query=q, category=category, min_price=min_price, max_price=max_price
    )
    categories = await repo.get_categories()
    return templates.TemplateResponse(
        request=request,
        name="shop/index.html",
        context={
            "request": request,
            "products": products,
            "categories": categories,
            "current_user": current_user,
            "q": q or "",
            "selected_category": category or "",
            "min_price": min_price or "",
            "max_price": max_price or ""
        }
    )

@router.get("/product/{product_id}")
async def get_product_detail(request: Request, product_id: int, db: AsyncSession = Depends(get_db)):
    """Hiển thị trang chi tiết của một sản phẩm cụ thể theo ID."""
    current_user = await auth_service.get_current_user(request, db)
    repo = ProductRepository(db)
    product = await repo.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return templates.TemplateResponse(
        request=request,
        name="shop/detail.html",
        context={
            "request": request,
            "product": product,
            "current_user": current_user
        }
    )
