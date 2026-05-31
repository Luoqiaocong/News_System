import json
from typing import Annotated, Optional
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from Config.DataBaseConfig import AsyncSessionLocal, get_db
from Exception import NewsException, ResponseCode
from Repo import NewsRepo, NewsCacheRepo, UserHistRepo
from Schemas.NewsSchema import CategoryData, NewsData, NewsDetailResponse, NewsListResponse, NewsListCard, RelatedNewsCard
from models.User import User
from Utils.ServiceDecorator import HandlerServiceException
from Utils.RedisUtil import redis_cache_decorator
from Utils.TransactionMixin import TransactionMixin


@HandlerServiceException
class NewsService(TransactionMixin):
    _business_exception_type = NewsException  # 定义当前服务的业务异常类型，TransactionMixin 会根据这个类型来决定哪些异常需要回滚事务

    '''
    依赖注入：
    1. NewsRepo：负责新闻相关的数据库操作
    2. UserHistRepo：负责用户历史记录的数据库操作
    3. AsyncSession：数据库会话，用于事务管理
    '''
    def __init__(self,
                repo: Annotated[NewsRepo, Depends()],
                Histrepo:Annotated[UserHistRepo, Depends()],
                db: Annotated[AsyncSession, Depends(get_db)]):
        self.repo = repo
        self.histrepo = Histrepo
        self.db = db

    @redis_cache_decorator(
        key_prefix="news:categories:{category_id}",
        expire=7200,  # 2小时过期
    )
    async def get_news_categories(self,category_id:int=0) -> list[CategoryData]:  
        categories_orm = await self.repo.get_categories(category_id) # 从数据库获取分类数据
        if not categories_orm:
            raise NewsException(code=ResponseCode.NEWS_CATEGORY_NOT_FOUND)
        return [CategoryData.model_validate(c) for c in categories_orm]

    async def get_news_list(self,category_id: int, page: int, page_size: int)->NewsListResponse:
        start = (page - 1) * page_size
        end = start + page_size - 1
    
        try:
            news_detail_lt, total = await NewsCacheRepo.get_news_list_cache(category_id, start, end)
        except Exception:
            from Utils.LogUtil import log
            log.warning("Redis 查询失败(get_news_list_cache)，降级到 DB")
            news_detail_lt, total = None, 0
        if news_detail_lt and total:
            valid = [d for d in news_detail_lt if d]
            expected = min(page_size, total - start)  # 计算当前页预期的有效数据数量  total - start 是为了处理最后一页不足 page_size 条的情况
            if len(valid) >= expected:  # 如果有效数据数量满足预期，直接返回缓存结果
                return NewsListResponse(
                    news_list=[NewsListCard.model_validate(json.loads(d)) for d in valid],  # 从缓存中获取的字符串需要先解析成字典，再转换成 Pydantic 模型
                    total=total)

        # 缓存未命中或缓存内容不足，走 DB
        news_orm_list, total = await self.repo.get_news(category_id, start, page_size)
        if news_orm_list:
            # 懒填充 ZSet 列表缓存，下次请求可命中
            try:
                all_ids = await self.repo.get_all_news_ids(category_id)
                await NewsCacheRepo.set_news_list_cache(category_id, all_ids)
            except Exception:
                from Utils.LogUtil import log
                log.warning("列表缓存填充失败，不影响本次返回")
            return NewsListResponse(
                news_list=[NewsListCard.model_validate(n) for n in news_orm_list],
                total=total)

        raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)

    async def get_news_detail(self, news_id:int):
        # ====== 1. 新闻详情（先缓存，后 DB）======
        try:
            detail_dict = await NewsCacheRepo.get_detail_cache(news_id)
        except Exception:
            from Utils.LogUtil import log
            log.warning("Redis 查询失败(get_detail_cache)，降级到 DB")
            detail_dict = None
        if detail_dict:
            # 缓存命中
            category_id = detail_dict.get("category_id")  # 从缓存中获取 category_id，后续获取相关新闻会用到
            if category_id is None:
                raise NewsException(code=ResponseCode.NEWS_CATEGORY_NOT_FOUND)
        else:
            # 缓存未命中，走 DB
            detail_orm = await self.repo.get_news_detail(news_id)
            if not detail_orm:
                raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)  
            category_id = detail_orm.category_id  # 从 DB 获取 category_id
            detail_dict = NewsData.model_validate(detail_orm).model_dump(mode="json")  # mode='json' 把 datetime 转成字符串
            # 写回缓存
            try:
                await NewsCacheRepo.set_detail_cache(news_id, detail_dict)
            except Exception:
                from Utils.LogUtil import log
                log.warning("Redis 写入失败(set_detail_cache)，不影响本次返回")

        # ====== 2. 相关新闻（先 Redis Set SRANDMEMBER，后 DB ORDER BY RAND()）======
        try:
            related = await NewsCacheRepo.get_related_news_cache(category_id, news_id)
        except Exception:
            from Utils.LogUtil import log
            log.warning("Redis 查询失败(get_related_news_cache)，降级到 DB")
            related = None
        if not related :
            # 缓存未命中，走 DB
            related = await self.repo.get_related_news(news_id, category_id)
            # 用刚取到的新闻 ID 增量预热 Set，不额外查全表
            related_ids = [i.id for i in related]
            if related_ids:
                try:
                    await NewsCacheRepo.warm_related_news(category_id, related_ids)
                except Exception:
                    from Utils.LogUtil import log
                    log.warning("Redis 写入失败(warm_related_news)，不影响本次返回")

        # ====== 3. 打包返回 ======
        return NewsDetailResponse(detail=NewsData.model_validate(detail_dict),related_news=[RelatedNewsCard.model_validate(r) for r in related])
    

    async def handle_news_view(
            self,
            news_id: int,
            user_id: Optional[int]
    ):
        """后台任务：使用独立 session，不占用请求连接池"""
        async with AsyncSessionLocal() as session:
            repo = NewsRepo(db=session)
            histrepo = UserHistRepo(db=session)

            # --- 1. 更新浏览量 (核心) ---
            success = await repo.update_views(news_id)
            if not success:
                return
            await session.commit()

            # 同步刷新 Redis 缓存中的浏览量
            try:
                await NewsCacheRepo.bump_views_cache(news_id)
            except Exception:
                from Utils.LogUtil import log
                log.warning("Redis 更新失败(bump_views_cache)，不影响本次浏览量记录")

            # --- 2. 记录历史 (附属) ---
            if user_id:
                is_add = await histrepo.add_view(news_id, user_id)
                if not is_add:
                    await histrepo.add_hist(news_id, user_id)
                await session.commit()

    async def search_news(self, query: str, category_id: int, start_date: Optional[str], end_date: Optional[str], page: int, page_size: int):
        
        start = (page - 1) * page_size

        rows, total = await self.repo.search(query, category_id, start_date, end_date, start, page_size)
        if not rows:
            raise NewsException(code=ResponseCode.NEWS_NOT_FOUND)
        return NewsListResponse(
            news_list=[NewsListCard.model_validate(n) for n in rows],
            total=total)
