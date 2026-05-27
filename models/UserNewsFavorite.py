from datetime import datetime
from sqlalchemy import DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from Config.DataBaseConfig import Base


class UserFavorite(Base):
    __tablename__ = "user_news_favorite"

    __table_args__ = (
        # 数据库级别约束：防止同一个用户对同一条新闻重复收藏
        UniqueConstraint("user_id","news_id",name="user_news_fav_unique"),
    )

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:Mapped[int] = mapped_column(Integer, ForeignKey("user.id",ondelete="CASCADE"),nullable=False,comment="用户id")
    news_id:Mapped[int] = mapped_column(Integer, ForeignKey("news.id",ondelete="CASCADE"),nullable=False,comment="新闻id")
    favorited_at :Mapped[datetime] = mapped_column(DateTime,nullable=False,default=datetime.now,comment="收藏时间")