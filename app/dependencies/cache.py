from fastapi import Depends
from redis.asyncio import Redis
import json
from typing import Optional, Any
from datetime import datetime, date
from decimal import Decimal

from app.redis import get_redis_client

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class CacheManager:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get_cached(self, key: str) -> Optional[dict]:
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    async def set_cached(self, key: str, data: Any, ttl: int = 3600):
        try:
            serialized_data = json.dumps(data, cls=JSONEncoder, ensure_ascii=False)
            await self.redis.set(key, serialized_data, ex=ttl)
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        keys = []
        async for key in self.redis.scan_iter(pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)

async def get_cache_manager(redis: Redis = Depends(get_redis_client)):
    return CacheManager(redis)