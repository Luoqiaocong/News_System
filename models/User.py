from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime,  Index
from sqlalchemy.orm import  Mapped, mapped_column


from Config.DataBaseConfig import Base

class TimeStamp(Base):
    __abstract__ = True  # 这只是一张公共字段类
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now,
                                                comment="修改时间")
    

# alter table user add column is_delete bool default FALSE,add column delete_time DATETIME default NULL;  软删除时添加
class User(TimeStamp):
    __tablename__ = "user"

    __table_args__ = (
        Index('uk_email_delete', 'email','deleted_at', unique=True),
    )
    # id: 主键自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="用户ID")

    # email: 不可为空，唯一
    email: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户邮箱")

    # password: 不可为空
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码")

    # nickname: 不可为空
    nickname: Mapped[str] = mapped_column(String(255) ,default="Seven用户",comment="昵称")

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

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True,comment="删除时间(NULL表示活跃)")  # 软删除时添加



    def soft_delete(self):
        """逻辑销毁：打上当前的 UTC 时间"""
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """一针还魂：清空删除时间，原地复活"""
        self.deleted_at = None


    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

