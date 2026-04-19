
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Index, ForeignKey
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy.sql.sqltypes import Text


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__="categories"  # 表名
    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True,comment="新闻类型ID")
    name:Mapped[str] = mapped_column(String(255),nullable=False,comment="新闻类型名称")

class News(Base):
    __tablename__="news"

    #  索引：新闻类型ID、发布时间索引，用于快速查询
    __table_args__ = (
        Index('fk_news_category_idx','category_id'),
        Index('fk_publish_time_idx','publish_time')
    )
    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True,comment="新闻ID")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey(Category.id), nullable=False, comment="新闻类型ID")
    title:Mapped[str] = mapped_column(String(255),nullable=False,comment="新闻标题")
    author:Mapped[Optional[str]] = mapped_column(String(255),nullable=False,comment="新闻发布栏目")
    publish_time:Mapped[datetime] = mapped_column(DateTime,default=datetime.now,comment="新闻发布时间")
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览量")
    summary:Mapped[Optional[str]] = mapped_column(Text,nullable=False,comment="新闻简介")
    content:Mapped[str] = mapped_column(Text,nullable=False,comment="新闻内容")
    thumbnail:Mapped[Optional[str]] = mapped_column(String(255),comment="新闻图片地址")

    #   重写__repr__方法，方便调试
    def __repr__(self):
        return f"News(id={self.id},title={self.title},author={self.author},publish_time={self.publish_time},summary={self.summary},content={self.content},views={self.views},category_id={self.category_id},thumbnail={self.thumbnail})"
        

