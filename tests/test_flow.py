import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product
from src.models.coupon import Coupon
from src.models.user import User
from src.models.order import Order, OrderItem
from src.services.auth_service import get_password_hash

@pytest.fixture(autouse=True)
async def seed_test_data(db_session: AsyncSession):
    """Khởi tạo trước các sản phẩm và mã giảm giá mẫu cho mỗi phiên kiểm thử."""
    await db_session.execute(delete(OrderItem))
    await db_session.execute(delete(Order))
    await db_session.execute(delete(Product))
    await db_session.execute(delete(Coupon))
    await db_session.execute(delete(User))
    await db_session.commit()

    p1 = Product(id=1, name="Test Product 1", price=100000.0, stock=5, category="Test")
    p2 = Product(id=2, name="Test Product 2", price=500000.0, stock=10, category="Test")
    db_session.add(p1)
    db_session.add(p2)
    
    c1 = Coupon(
        id=1,
        code="TEST20",
        discount_type="percentage",
        discount_value=20.0,
        min_order_value=150000.0,
        max_discount_amount=50000.0,
        usage_limit=2,
        used_count=0,
        is_active=True
    )
    c2 = Coupon(
        id=2,
        code="TESTFIXED",
        discount_type="fixed_amount",
        discount_value=50000.0,
        min_order_value=100000.0,
        usage_limit=10,
        used_count=0,
        is_active=True
    )
    db_session.add(c1)
    db_session.add(c2)
    await db_session.commit()

@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient, db_session: AsyncSession):
    """Kiểm tra luồng đăng ký tài khoản mới và đăng nhập nhận cookie JWT thành công."""
    reg_data = {
        "full_name": "Test User",
        "email": "testuser@example.com",
        "password": "password123"
    }
    response = await client.post("/register", data=reg_data)
    assert response.status_code == 303
    
    res = await db_session.execute(select(User).filter(User.email == "testuser@example.com"))
    user = res.scalars().first()
    assert user is not None
    assert user.full_name == "Test User"
    
    login_data = {
        "email": "testuser@example.com",
        "password": "password123"
    }
    response = await client.post("/login", data=login_data)
    assert response.status_code == 303
    assert "access_token" in response.cookies

@pytest.mark.asyncio
async def test_cart_operations(client: AsyncClient):
    """Kiểm tra các thao tác thêm, cập nhật số lượng và xóa sản phẩm khỏi giỏ hàng."""
    add_resp = await client.post("/api/cart/add", json={"product_id": 1, "quantity": 2})
    assert add_resp.status_code == 200
    assert add_resp.json()["success"] is True
    assert add_resp.json()["new_quantity"] == 2
    
    update_resp = await client.post("/api/cart/update", json={"product_id": 1, "quantity": 3})
    assert update_resp.status_code == 200
    assert update_resp.json()["new_quantity"] == 3
    
    view_resp = await client.get("/cart")
    assert view_resp.status_code == 200
    assert "Test Product 1" in view_resp.text

@pytest.mark.asyncio
async def test_coupon_validation_and_application(client: AsyncClient):
    """Kiểm tra tính đúng đắn khi áp dụng và xác thực các điều kiện của mã giảm giá."""
    await client.post("/api/cart/add", json={"product_id": 1, "quantity": 1})
    
    fail_resp = await client.post("/api/cart/apply-coupon", json={"code": "TEST20"})
    assert fail_resp.status_code == 400
    
    await client.post("/api/cart/add", json={"product_id": 1, "quantity": 1})
    
    success_resp = await client.post("/api/cart/apply-coupon", json={"code": "TEST20"})
    assert success_resp.status_code == 200
    assert success_resp.json()["discount_amount"] == 40000.0

@pytest.mark.asyncio
async def test_checkout_and_stock_deduction(client: AsyncClient, db_session: AsyncSession):
    """Kiểm tra giao dịch checkout, đảm bảo cập nhật kho và lưu đơn hàng chính xác."""
    reg_data = {"full_name": "Buyer", "email": "buyer@example.com", "password": "password123"}
    await client.post("/register", data=reg_data)
    
    login_data = {"email": "buyer@example.com", "password": "password123"}
    login_resp = await client.post("/login", data=login_data)
    
    await client.post("/api/cart/add", json={"product_id": 1, "quantity": 2})
    await client.post("/api/cart/apply-coupon", json={"code": "TESTFIXED"})
    
    checkout_data = {
        "shipping_address": "123 Hanoi Street",
        "recipient_name": "Buyer Name",
        "recipient_phone": "0987654321"
    }
    checkout_resp = await client.post("/api/order/checkout", json=checkout_data)
    assert checkout_resp.status_code == 200
    order_id = checkout_resp.json()["order_id"]
    
    db_session.expire_all()
    
    prod_res = await db_session.execute(select(Product).filter(Product.id == 1))
    product = prod_res.scalars().first()
    assert product.stock == 3
    
    coupon_res = await db_session.execute(select(Coupon).filter(Coupon.id == 2))
    coupon = coupon_res.scalars().first()
    assert coupon.used_count == 1
    
    order_res = await db_session.execute(select(Order).filter(Order.id == order_id))
    order = order_res.scalars().first()
    assert order is not None
    assert order.total_amount == 200000.0
    assert order.discount_amount == 50000.0
    assert order.final_amount == 150000.0
