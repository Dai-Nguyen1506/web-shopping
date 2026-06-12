import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.database import engine, Base
from src.routers.web import views_auth, views_shop, views_cart, views_admin
from src.routers.api import api_cart, api_order

app = FastAPI(title="E-Shop Premium API", version="1.0.0")

current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
async def on_startup():
    """Tạo lập các bảng cơ sở dữ liệu khi khởi động ứng dụng nếu chưa tồn tại."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(views_auth.router)
app.include_router(views_shop.router)
app.include_router(views_cart.router)
app.include_router(views_admin.router)
app.include_router(api_cart.router)
app.include_router(api_order.router)
