from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Cấu hình toàn hệ thống."""
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecommerce.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "super-secret-key-change-it-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
