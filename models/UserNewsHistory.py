from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from Config.DataBaseConfig import Base


class UserNewsHistory(Base):
    __tablename__ = 'user_news_history'

    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="user_news_hist_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="id")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False,
                                         comment="用户Id")
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False,
                                         comment="新闻id")
    viewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, comment="浏览时间")
