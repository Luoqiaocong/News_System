
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column

class Base(DeclarativeBase):
    pass

class TimeStamp(Base):
    __abstract__ = True  # 这只是一张公共字段类
    create_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    update_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now,
                                                comment="修改时间")

class Category(Base):
    __tablename__="categories"  # 表名
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    name:Mapped[str] = mapped_column(String)
    description:Mapped[str] = mapped_column(String)
