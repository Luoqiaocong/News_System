import json
import time
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.News import Category, News  # 替换为你实际的模型导入路径
from Utils.RedisUtil import redis_client  # 替换为你实际的 redis 实例


async def warmup_all_categories_and_news(db: AsyncSession):
    print("====== 开始执行全量架构预热 [纯净查库版] ======")
    start_time = time.time()

    # 1. 使用异步方式查询所有的类别
    result = await db.execute(select(Category))
    categories = result.scalars().all()

    if not categories:
        print("数据库中无类别数据，预热终止。")
        return

    # 2. 使用异步方式查询所有新闻 (严格对齐你截图中的 columns)
    result = await db.execute(select(News))
    all_news = result.scalars().all()

    # 3. 在内存中按 category_id 将新闻进行归类 (减少与数据库的交互)
    category_news_map = defaultdict(list)
    for news in all_news:
        category_news_map[news.category_id].append(news)

    # 4. 预热类别树结构（news:tree:categories）
    categories_data = [{"id": cat.id, "name": cat.name} for cat in categories]
    await redis_client.set("news:tree:categories", json.dumps(categories_data))

    total_news_count = 0

    # 5. 遍历每个类别，把对应的列表和详情刷进 Redis
    for category in categories:
        category_zset_key = f"news:list:{category.id}"
        global_zset_key = "news:list:all"

        # 从刚才分类好的字典里，直接拿到这个类别下的所有新闻列表
        news_in_category = category_news_map[category.id]

        # 为每个类别准备 ZSet 数据
        category_zset_data = {}
        global_zset_data = {}

        for news in news_in_category:
            total_news_count += 1
            news_id_str = str(news.id)

            # 将新闻发布时间转换为 Unix 时间戳作为 Zset 排序的 Score
            score = int(time.mktime(news.publish_time.timetuple()))

            # a. 添加到类别 Zset 数据
            category_zset_data[news_id_str] = score

            # b. 添加到全局 Zset 数据
            global_zset_data[news_id_str] = score

            # c. 严格对齐你 news 表的 9 个基础字段，序列化为详情 String
            detail_key = f"news:detail:{news.id}"
            news_json = json.dumps({
                "id": news.id,
                "category_id": news.category_id,
                "title": news.title,
                "author": news.author,
                "publish_time": news.publish_time.strftime("%Y-%m-%d %H:%M:%S"),
                "views": news.views,
                "summary": news.summary,
                "content": news.content,
                "thumbnail": news.thumbnail
            })

            # 直接设置详情缓存，过期时间 86400 秒（1天）
            await redis_client.set(detail_key, news_json, expire=86400)

        # 批量添加 ZSet 数据
        if category_zset_data:
            # 使用底层 Redis 连接的 zadd 方法
            await redis_client._redis.zadd(category_zset_key, category_zset_data)

        if global_zset_data:
            # 使用底层 Redis 连接的 zadd 方法
            await redis_client._redis.zadd(global_zset_key, global_zset_data)

    end_time = time.time()
    print("====== 预热圆满成功 ======")
    print(f"耗时: {end_time - start_time:.2f} 秒")
    print(f"已缓存类别: {len(categories)} 个")
    print(f"已缓存新闻详情和双向索引: {total_news_count} 条")
