from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    postgres_user: str = "fl0_user"
    postgres_password: str = "fl0_password"
    postgres_db: str = "fl0_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Telegram
    telegram_bot_token: str
    
    # YooKassa (optional - can be set later)
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    
    # Webhook
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Security
    rate_limit_requests: int = 5
    rate_limit_window: int = 60  # seconds
    
    # App
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

