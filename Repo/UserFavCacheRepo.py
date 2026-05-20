from Utils.RedisUtil import redis_client

class UserFavCacheRepo:
    """
    用户收藏缓存仓库
    """
    @staticmethod
    async def add_fav_cache(news_id:int,user_id:int):
        key = f"user:fav:{user_id}"
        await redis_client.sadd(key, news_id)