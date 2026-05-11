import json
from typing import Any, Optional
from redis import asyncio as aioredis
from Config.settings import settings


class RedisManager:
    """
    Redis 异步封装类
    """

    def __init__(self):
        # 初始化连接池
        self._redis: Optional[aioredis.Redis] = None

    async def init_redis(self):
        """初始化 Redis 连接（在 FastAPI 启动钩子中调用）"""
        self._redis = aioredis.Redis(
            host=settings.REDIS_HOST,  # redis服务地址
            port=settings.REDIS_PORT,  # redis端口
            db=settings.REDIS_DB,  # redis数据库
            decode_responses=True  # 是否对返回数据进行解码
        )

    async def close(self):
        """关闭连接（在 FastAPI 关闭钩子中调用）"""
        if self._redis:
            await self._redis.close()

    async def set(self, key: str, value: Any, expire: int = None):
        """
        设置缓存
        value: 支持 list, dict, str, int 等自动转 JSON
        expire: 过期时间（秒）
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        await self._redis.set(key, value, ex=expire)

    async def get(self, key: str) -> Any:
        """获取缓存并自动尝试解析 JSON"""
        data = await self._redis.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data

    async def delete(self, key: str):
        """删除缓存"""
        await self._redis.delete(key) if await self.exists(key) else None


    async def exists(self, key: str) -> bool:
        """检查是否存在"""
        return await self._redis.exists(key) > 0


# 全局单例
redis_client = RedisManager()
