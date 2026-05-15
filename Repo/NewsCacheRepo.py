import json
from typing import List, Optional
from Utils.RedisUtil import redis_client


class NewsCacheRepo:
    """
    新闻缓存仓库 - 专门处理 Redis 缓存操作
    职责：管理新闻相关的 Redis 缓存读写
    """
    @staticmethod
    async def get_news_list_cache(category_id: int|None,start: int, end: int):
            # 构建Zset键
            zset_key = f"news:list:{category_id}" if category_id is not None else "news:list:all"

            total = await redis_client.zcard(zset_key)  # 获取新闻总数
            if not total:
                return None,0

            # 从Redis获取新闻ID列表
            news_ids = await redis_client.zrevrange(zset_key, start, end)
            if not news_ids:
                return None,total

            # 批量获取新闻详情
            detail_keys = [f"news:detail:{nid.decode('utf-8') if isinstance(nid, bytes) else nid}" for nid in news_ids]
            news_detail_list = await redis_client.mget(*detail_keys)

            return news_detail_list, total


