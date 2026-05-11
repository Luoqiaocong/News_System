import logging
from typing import Annotated, Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from Repo import NewsRepo, UserHistoryRepo
from Schemas.UserSchema import UserInfo


class NewsService:
    def __int__(self):
        pass


    async def handle_news_view(
            self,
            db: AsyncSession,
            news_id: int,
            user:UserInfo
    ):
        """
        统一处理浏览逻辑：
        1. 增加浏览量 (核心逻辑)
        2. 如果有 user_id，记录历史 (附属逻辑)
        """
        # --- 1. 更新浏览量 (核心) ---
        success = await NewsRepo.update_views(db, news_id)
        if not success:
            raise HTTPException(status_code=404, detail="该新闻不存在")

        # 立即提交浏览量，保住核心数据
        await db.commit()

        # --- 2. 记录历史 (附属) ---
        if user and user.id:
            try:
                await UserHistoryRepo.add_view(news_id,user.id, db)
                # 历史记录成功/更新后，提交历史记录的事务
                await db.commit()
            except Exception as e:
                # 万一发生其他意外（如数据库断开），确保回滚并静默
                await db.rollback()
                logging.error(f"\'{user.email}\'记录浏览历史失败，失败原因-->{e}")
