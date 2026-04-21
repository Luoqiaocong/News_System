from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime,  Index, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class TimeStamp(Base):
    __abstract__ = True  # 这只是一张公共字段类
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now,
                                                comment="修改时间")


class User(TimeStamp):
    __tablename__ = "users"

    __table_args__ = (
        Index("idx_user_name", "username", unique=True),
    )
    # id: 主键自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="用户ID")

    # username: 不可为空，唯一
    username: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户名")

    # password: 不可为空
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="哈希密码")

    # nickname: 不可为空
    nickname: Mapped[str] = mapped_column(
        String(255) ,default="未命名用户",comment="昵称"
    )

    # avatar: 不可为空,默认头像
    avatar: Mapped[str] = mapped_column(
        String(255),
        default="https://www.gravatar.com/avatar/0000?d=mp&f=y",
        comment="头像URL"
    )

    # bio: 可为空,默认值为一段话
    bio: Mapped[Optional[str]] = mapped_column(
        String(500),
        default="这个人很懒，什么都没有留下...",
        comment="个人简介"
    )


    def __repr__(self):
        return f"<User(username='{self.username}',nickname='{self.nickname}')>"


class UserToken(Base):
    __tablename__ = "user_token"

    id:Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="登录凭证ID")
    user_id:Mapped[int] = mapped_column(Integer, ForeignKey("users.id"),nullable=False, comment="用户ID")
    token: Mapped[str] = mapped_column(String(255), nullable=False, comment="登录凭证Token")
    expire_at:Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    created_at:Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")

