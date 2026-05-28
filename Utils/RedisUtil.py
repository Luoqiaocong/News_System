from redis import asyncio as aioredis
from Config.settings import settings
import json
import functools
import inspect
from typing import Any, Callable, Optional


class RedisManager:
    """
    Redis 异步管理器

    设计理念：
    1. 直接暴露原生 Redis 客户端，支持所有 Redis 命令
    2. 仅提供少量高频业务的便捷方法（如 set/get 的自动序列化）
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def init_redis(self):
        """初始化 Redis 连接（在 FastAPI 启动钩子中调用）"""
        self._redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    async def close(self):
        """关闭连接（在 FastAPI 关闭钩子中调用）"""
        if self._redis:
            await self._redis.close()

    # @property
    # def client(self) -> aioredis.Redis:
    #     """
    #     直接暴露原生 Redis 客户端
    #     用法：await redis_client.client.zadd(...) 或任何 Redis 命令
    #     """
    #     if not self._redis:
    #         raise RuntimeError("Redis 未初始化，请先调用 init_redis()")
    #     return self._redis

    # ========== 高频便捷方法（带自动序列化）==========

    async def set(self, key: str, value: Any, expire: int = None):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        if expire:
            await self._redis.set(key, value, ex=expire)
        else:
            await self._redis.set(key, value)

    async def get(self, key: str) -> Any:
        """
        获取缓存（自动尝试 JSON 反序列化）

        :param key: 缓存键
        :return: 解析后的数据，失败返回原始字符串
        """
        data = await self._redis.get(key)
        if not data:
            return None
        
        # 🌟 核心优化：先用 strip() 剔除两端空格，然后判断是否以 { 或 [ 开头
        # 如果不是，说明它压根就不是字典或列表，连 json.loads 都懒得调，直接原样返回
        clean_data = data.strip()
        if not (clean_data.startswith("{") or clean_data.startswith("[")):
            return data

        try:
            # 能走到这里的，百分之百是准备解析成 dict 或 list 的字符串
            return json.loads(clean_data)
        except (json.JSONDecodeError, TypeError):
            # 极少数情况下，虽然以 { 开头但可能是不合法的 JSON（脏数据），防御性返回原字符串
            return data

    async def delete(self, *keys: str):
        """删除一个或多个缓存键"""
        if keys:
            await self._redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self._redis.exists(key) > 0

    # ========== 动态方法代理==========

    def __getattr__(self, name: str):
        """
        动态代理所有未显式封装的 Redis 命令

        用法示例：
        - await redis_client.hset('user:1', 'name', 'Alice')
        - await redis_client.lpush('queue', 'task1')
        - await redis_client.sadd('tags', 'python', 'fastapi')

        这样就不需要为每个 Redis 命令单独写封装了！
        """
        if self._redis is None:
            raise RuntimeError("Redis 未初始化，请先调用 init_redis()")

        # 直接返回原生 Redis 客户端的对应方法
        return getattr(self._redis, name)


# 全局单例
redis_client = RedisManager()


def redis_cache_decorator(
        key_prefix: str,
        expire: int = 3600,
        to_dict: bool = True,
):
    """
    异步通用缓存装饰器

    工作流：
    1. 拦截请求 -> 2. 构建 Key -> 3. 查 Redis -> 4. 命中则直接返回 -> 5. 未命中则执行函数并存 Redis
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            cache_key = key_prefix
            for param_name, param_value in bound_args.arguments.items():
                placeholder = f"{{{param_name}}}"
                if placeholder in cache_key:
                    val_str = str(param_value) if param_value is not None else "all"
                    cache_key = cache_key.replace(placeholder, val_str)

            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data is not None:
                    return cached_data
            except Exception as e:
                from Utils.LogUtil import log
                log.warning(f"Redis 缓存查询失败，降级到数据库查询: {e}")

            result = await func(*args, **kwargs)

            try:
                if result is not None:
                    if to_dict:
                        if isinstance(result, list):
                            cache_value = [
                                item.model_dump() if hasattr(item, 'model_dump') else item
                                for item in result
                            ]
                        else:
                            cache_value = result.model_dump() if hasattr(result, 'model_dump') else result
                    else:
                        cache_value = result

                    await redis_client.set(cache_key, cache_value, expire=expire)
            except Exception as e:
                from Utils.LogUtil import log
                log.warning(f"Redis 缓存写入失败，下次请求将无法命中缓存: {e}")

            return result

        return wrapper

    return decorator
