import json
import redis.asyncio as aioredis
from src.config import settings

class MockRedis:
    """Mock Redis in-memory client giả lập các phương thức cơ bản của Redis."""
    
    def __init__(self):
        """Khởi tạo kho lưu trữ dữ liệu giả lập."""
        self.store = {}

    async def ping(self):
        """Kiểm tra kết nối giả lập."""
        return True

    async def get(self, name):
        """Lấy giá trị của một key dạng string."""
        return self.store.get(name)

    async def set(self, name, value, ex=None):
        """Đặt giá trị cho một key dạng string."""
        self.store[name] = str(value)
        return True

    async def delete(self, *names):
        """Xóa một hoặc nhiều key."""
        count = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                count += 1
        return count

    async def hget(self, name, key):
        """Lấy giá trị của một trường trong hash."""
        hash_dict = self.store.get(name, {})
        val = hash_dict.get(key)
        return str(val) if val is not None else None

    async def hset(self, name, key=None, value=None, mapping=None):
        """Đặt giá trị cho một hoặc nhiều trường trong hash."""
        if name not in self.store:
            self.store[name] = {}
        if mapping:
            for k, v in mapping.items():
                self.store[name][k] = str(v)
            return len(mapping)
        else:
            self.store[name][key] = str(value)
            return 1

    async def hgetall(self, name):
        """Lấy tất cả các cặp trường và giá trị trong hash."""
        return {k.encode(): v.encode() for k, v in self.store.get(name, {}).items()}

    async def hdel(self, name, *keys):
        """Xóa một hoặc nhiều trường trong hash."""
        if name not in self.store:
            return 0
        count = 0
        for key in keys:
            if key in self.store[name]:
                del self.store[name][key]
                count += 1
        return count

    async def hincrby(self, name, key, amount=1):
        """Tăng giá trị số của một trường trong hash."""
        if name not in self.store:
            self.store[name] = {}
        current = int(self.store[name].get(key, 0))
        new_val = current + amount
        self.store[name][key] = str(new_val)
        return new_val

    async def keys(self, pattern):
        """Lọc danh sách các key theo pattern."""
        import fnmatch
        return [k.encode() for k in self.store.keys() if fnmatch.fnmatch(k, pattern.replace("*", "*"))]

    async def flushdb(self):
        """Xóa sạch toàn bộ cơ sở dữ liệu giả lập."""
        self.store.clear()
        return True

_mock_redis_client = None

async def get_redis_client():
    """Khởi tạo và trả về client Redis thực tế hoặc Client giả lập nếu lỗi kết nối."""
    global _mock_redis_client
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        return client
    except Exception:
        if _mock_redis_client is None:
            _mock_redis_client = MockRedis()
        return _mock_redis_client
