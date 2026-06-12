import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import Base, get_db
from src.main import app
from src.redis import MockRedis, get_redis_client

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testmemdb?mode=memory&cache=shared"
engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Cung cấp database session test trong bộ nhớ cho việc kiểm thử."""
    async with TestingSessionLocal() as session:
        yield session
        await session.commit()

mock_redis_instance = MockRedis()

async def override_get_redis_client():
    """Trả về client Redis giả lập dùng riêng cho quá trình kiểm thử."""
    return mock_redis_instance

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis_client] = override_get_redis_client

@pytest.fixture(scope="session")
def event_loop():
    """Tạo vòng lặp sự kiện asyncio có vòng đời khớp với toàn bộ phiên test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

persistent_conn = None

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Khởi tạo cấu trúc bảng dữ liệu trong bộ nhớ SQLite trước khi chạy test."""
    global persistent_conn
    persistent_conn = await engine.connect()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    if persistent_conn:
        await persistent_conn.close()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Cung cấp session database cô lập riêng biệt cho từng hàm test."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Cung cấp httpx AsyncClient để gửi request bất đồng bộ tới ứng dụng."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def clear_redis():
    """Dọn sạch dữ liệu trong kho Redis giả lập sau mỗi hàm test."""
    await mock_redis_instance.flushdb()
    yield
