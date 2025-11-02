import redis.asyncio as redis
from app.config import Config


async def get_redis():
    """Простое подключение к Redis"""
    redis_client = redis.from_url(
        Config.REDIS_URL, 
        decode_responses=True
    )
    try:
        await redis_client.ping()
        print("Connected to Redis")
        return redis_client
    except Exception as e:
        print(f"Redis connection error: {e}")
        raise

async def get_redis_client():
    """Dependency для FastAPI"""
    redis_client = await get_redis()
    try:
        yield redis_client
    finally:
        await redis_client.aclose()