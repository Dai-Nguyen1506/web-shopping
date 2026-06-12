import asyncio
from datetime import datetime, timedelta
from src.database import engine, Base, SessionLocal
from src.models.user import User
from src.models.product import Product
from src.models.coupon import Coupon
from src.services.auth_service import get_password_hash

async def seed_data():
    """Tạo mới các bảng database và khởi tạo dữ liệu mẫu cho hệ thống bán hàng."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        admin = User(
            email="admin@eshop.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Quản Trị Viên",
            is_admin=True
        )
        user = User(
            email="user@eshop.com",
            hashed_password=get_password_hash("user123"),
            full_name="Nguyễn Văn A",
            is_admin=False
        )
        db.add(admin)
        db.add(user)
        products = [
            Product(
                name="Điện thoại iPhone 15 Pro Max",
                description="Bộ nhớ 256GB, phiên bản Titan tự nhiên cực kỳ sang trọng.",
                price=30000000.0,
                stock=10,
                category="Điện thoại",
                image_url=""
            ),
            Product(
                name="Máy tính Macbook Pro 14 M3",
                description="Chip Apple M3 mạnh mẽ, RAM 16GB, SSD 512GB cho lập trình viên.",
                price=45000000.0,
                stock=5,
                category="Laptop",
                image_url=""
            ),
            Product(
                name="Tai nghe không dây Sony WH-1000XM5",
                description="Khả năng chống ồn chủ động đỉnh cao, pin sử dụng liên tục 30 giờ.",
                price=8500000.0,
                stock=15,
                category="Phụ kiện",
                image_url=""
            ),
            Product(
                name="Giày Thể Thao Nike Air Force 1",
                description="Thiết kế cổ điển màu trắng tinh khôi, thoải mái khi di chuyển.",
                price=2900000.0,
                stock=20,
                category="Thời trang",
                image_url=""
            ),
            Product(
                name="Áo Hoodie Adidas Essentials",
                description="Chất liệu cotton pha nỉ ấm áp, thiết kế logo cỏ ba lá đặc trưng.",
                price=1500000.0,
                stock=30,
                category="Thời trang",
                image_url=""
            )
        ]
        for p in products:
            db.add(p)
        coupons = [
            Coupon(
                code="GIAM20",
                discount_type="percentage",
                discount_value=20.0,
                min_order_value=1000000.0,
                max_discount_amount=500000.0,
                usage_limit=100,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now() + timedelta(days=30),
                is_active=True
            ),
            Coupon(
                code="ESHOP100",
                discount_type="fixed_amount",
                discount_value=100000.0,
                min_order_value=500000.0,
                usage_limit=50,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now() + timedelta(days=30),
                is_active=True
            ),
            Coupon(
                code="VIP500",
                discount_type="fixed_amount",
                discount_value=500000.0,
                min_order_value=5000000.0,
                usage_limit=10,
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now() + timedelta(days=30),
                is_active=True
            )
        ]
        for c in coupons:
            db.add(c)
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed_data())
