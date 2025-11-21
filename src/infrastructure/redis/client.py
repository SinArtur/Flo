import redis.asyncio as redis
from typing import Optional
from src.config.settings import settings


class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.client:
            await self.connect()
        return await self.client.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None):
        """Set value in Redis with optional expiration"""
        if not self.client:
            await self.connect()
        await self.client.set(key, value, ex=ex)
    
    async def increment(self, key: str, ex: Optional[int] = None) -> int:
        """Increment counter and set expiration"""
        if not self.client:
            await self.connect()
        count = await self.client.incr(key)
        if ex and count == 1:  # Set expiration only on first increment
            await self.client.expire(key, ex)
        return count
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            await self.connect()
        return bool(await self.client.exists(key))

