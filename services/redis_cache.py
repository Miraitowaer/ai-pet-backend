import redis.asyncio as redis
from config import settings

# 初始化异步 Redis 客户端
# decode_responses=True 能够让我们直接拿到字符串，而不是 bytes 格式
redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

async def get_cached_response(session_id: str, message: str) -> str:
    """
    尝试从 Redis 缓存中获取回答。
    适用场景：高频且无状态的问题（例如用户疯狂点击发送极其相似的短口令）
    """
    # 构建独一无二的 Cache Key，确保不同用户的问题不被互相串联
    cache_key = f"pet_cache:{session_id}:{message}"
    cached_reply = await redis_client.get(cache_key)
    return cached_reply

async def set_cached_response(session_id: str, message: str, reply: str, ttl: int = 3600):
    """
    将大模型的回答存入 Redis，并设置 TTL(生存时间)。
    默认缓存 1 小时 (3600秒)。防止过期数据长期占用珍贵的内存。
    """
    cache_key = f"pet_cache:{session_id}:{message}"
    # 使用 set 命令，并附带 ex (过期时间) 参数
    await redis_client.set(cache_key, reply, ex=ttl)
