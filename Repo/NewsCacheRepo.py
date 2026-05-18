import json
from typing import List, Optional
from Utils.RedisUtil import redis_client


class NewsCacheRepo:
    """
    新闻缓存仓库 - 专门处理 Redis 缓存操作
    职责：管理新闻相关的 Redis 缓存读写，不碰任何 DB 逻辑
    """

    # ========== 列表缓存（ZSet） ==========
    @staticmethod
    async def get_news_list_cache(category_id: int|None, start: int, end: int):
        zset_key = f"news:list:{category_id}" if category_id is not None else "news:list:all"
        total = await redis_client.zcard(zset_key)
        if not total:
            return None, 0
        news_ids = await redis_client.zrevrange(zset_key, start, end)
        if not news_ids:
            return None, total
        detail_keys = [f"news:detail:{nid.decode('utf-8') if isinstance(nid, bytes) else nid}" for nid in news_ids]
        news_detail_list = await redis_client.mget(*detail_keys)
        return news_detail_list, total

    # ========== 详情缓存（String） ==========
    @staticmethod
    async def get_detail_cache(news_id: int):
        key = f"news:detail:{news_id}"
        return await redis_client.get(key)

    @staticmethod
    async def set_detail_cache(news_id: int, data: dict, expire: int = 3600):
        key = f"news:detail:{news_id}"
        await redis_client.set(key, data, expire=expire)

    @staticmethod
    async def delete_detail_cache(news_id: int):
        key = f"news:detail:{news_id}"
        await redis_client.delete(key)

    # ========== 相关新闻缓存（Set + SRANDMEMBER） ==========
    @staticmethod
    async def get_related_news_cache(category_id: int, exclude_id: int, fetch_count: int = 12):
        """
        从 Redis Set 中随机取相关新闻。
        因为需要排除当前新闻，所以多取几个 fetch_count，再截取 6 条。
        返回 list[dict]（从 news:detail 反序列化），或 None 表示缓存未命中。
        """
        set_key = f"news:related:{category_id}"
        raw_ids = await redis_client.srandmember(set_key, fetch_count)
        if not raw_ids:
            return None

        ids = [int(nid) for nid in raw_ids if int(nid) != exclude_id][:6]
        if not ids:
            return []

        detail_keys = [f"news:detail:{nid}" for nid in ids]
        details = await redis_client.mget(*detail_keys)
        result = []
        for d in details:
            if d:
                try:
                    result.append(json.loads(d) if isinstance(d, str) else d)
                except (json.JSONDecodeError, TypeError):
                    pass
        return result if result else None

    @staticmethod
    async def warm_related_news(category_id: int, news_ids: list[int], expire: int = 86400):
        """
        将某分类下的所有新闻 ID 写入 Redis Set，供 SRANDMEMBER 随机取。
        """
        set_key = f"news:related:{category_id}"
        str_ids = [str(nid) for nid in news_ids]
        if str_ids:
            await redis_client.sadd(set_key, *str_ids)
            # 防止过期后一直是空 Set 导致每次都查 DB
            await redis_client.expire(set_key, expire)
