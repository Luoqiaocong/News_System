from redis import asyncio as aioredis
from Config.settings import settings
import json
import functools
import inspect
from typing import Any, Callable, Optional


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
            parsed = json.loads(data)
            if isinstance(parsed, (dict, list)):
                return parsed
            return data
        except (json.JSONDecodeError, TypeError):
            return data

    async def delete(self, key: str):
        """删除缓存"""
        await self._redis.delete(key) if await self.exists(key) else None


    async def exists(self, key: str) -> bool:
        """检查是否存在"""
        return await self._redis.exists(key) > 0

    async def zadd(self, key: str, mapping: dict):
        """
        向 ZSet 中添加成员
        mapping: {member: score, ...}
        """
        await self._redis.zadd(key, mapping)

    async def zrevrange(self, key: str, start: int, end: int, withscores: bool = False):
        """
        按分数从高到低获取 ZSet 中的成员
        start: 起始索引
        end: 结束索引
        withscores: 是否返回分数
        """
        return await self._redis.zrevrange(key, start, end, withscores=withscores)

    async def mget(self, *keys: str):
        """
        批量获取多个键的值
        """
        return await self._redis.mget(*keys)

    async def pipeline(self):
        """
        创建 Redis 管道对象
        返回底层的 Pipeline 对象
        """
        return self._redis.pipeline()

# 全局单例
redis_client = RedisManager()


def redis_cache_decorator(
        key_prefix: str,
        expire: int = 3600,
        to_dict: bool = True, # 存入缓存时的序列化控制
):
    """
    异步通用缓存装饰器

    工作流：
    1. 拦截请求 -> 2. 构建 Key -> 3. 查 Redis -> 4. 命中则直接返回 -> 5. 未命中则执行函数并存 Redis
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # --- 1. 动态构建缓存 Key ---
            # 获取函数的签名（参数结构）
            sig = inspect.signature(func)
            # 将传入的实参和形参进行绑定
            bound_args = sig.bind(*args, **kwargs)
            # 补全没传的默认参数
            bound_args.apply_defaults()

            # 遍历 key_prefix，将类似 {category_id} 的占位符替换为实际的值
            cache_key = key_prefix
            for param_name, param_value in bound_args.arguments.items():
                placeholder = f"{{{param_name}}}"
                if placeholder in cache_key:
                    # 转换逻辑：None 转为 "all"，其余转字符串
                    val_str = str(param_value) if param_value is not None else "all"
                    cache_key = cache_key.replace(placeholder, val_str)

            # --- 2. 缓存查询阶段 ---
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data is not None:
                    return cached_data  # 从缓存中查找结果了，直接返回，原始函数将不被执行
            except Exception as e:
                # Redis 查询失败，记录日志但不影响业务流程，继续执行原函数
                from Utils.LogUtil import log
                log.warning(f"Redis 缓存查询失败，降级到数据库查询: {e}")

            # --- 3. 原始函数执行阶段 ---
            result = await func(*args, **kwargs)

            # --- 4. 结果持久化阶段 ---
            try:
                if result is not None:
                    # 判定是否需要序列化（Pydantic 模型通常需要转 dict）
                    if to_dict:
                        if isinstance(result, list):
                            # 处理列表：如果是 Pydantic 模型则 model_dump，否则保留原样
                            cache_value = [
                                item.model_dump() if hasattr(item, 'model_dump') else item
                                for item in result
                            ]
                        else:
                            # 处理单体对象
                            cache_value = result.model_dump() if hasattr(result, 'model_dump') else result
                    else:
                        cache_value = result

                    # 异步存入 Redis
                    await redis_client.set(cache_key, cache_value, expire=expire)
            except Exception as e:
                # Redis 写入失败，记录日志但不影响返回结果
                from Utils.LogUtil import log
                log.warning(f"Redis 缓存写入失败，下次请求将无法命中缓存: {e}")

            return result

        return wrapper

    return decorator

