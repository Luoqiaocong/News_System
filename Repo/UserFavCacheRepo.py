from Utils.RedisUtil import redis_client


class UserFavCacheRepo:

    @staticmethod
    def _key(user_id: int) -> str:
        return f"user:fav:{user_id}"

    @staticmethod
    async def exists(user_id: int) -> bool:
        return await redis_client.exists(UserFavCacheRepo._key(user_id))

    @staticmethod
    async def is_member(news_id: int, user_id: int) -> bool:
        return await redis_client.sismember(UserFavCacheRepo._key(user_id), news_id)

    @staticmethod
    async def add(news_id: int, user_id: int):
        key = UserFavCacheRepo._key(user_id)
        await redis_client.srem(key, "-1")  # 清除占用位（如果有） -- 破防
        await redis_client.sadd(key, news_id)
        

    @staticmethod
    async def remove(news_ids: list[int], user_id: int):
        await redis_client.srem(UserFavCacheRepo._key(user_id), *news_ids)

    @staticmethod
    async def remove_all(user_id: int):
        await redis_client.delete(UserFavCacheRepo._key(user_id))

    @staticmethod
    async def write(user_id: int, news_ids: list[int]):
        """写入缓存（调用前确保 key 不存在）"""
        key = UserFavCacheRepo._key(user_id)
        if news_ids:
            await redis_client.sadd(key, *news_ids)
        else:
            await redis_client.sadd(key, "-1")  # 占位，防止每次去查数据库
            await redis_client.expire(key, 3600)  # 设置过期时间，避免死占位--布防

    @staticmethod
    async def count(user_id: int) -> int:
        return await redis_client.scard(UserFavCacheRepo._key(user_id))
    
