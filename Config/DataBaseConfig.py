from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from Config.settings import settings


# ==================== 数据库配置 ====================
ASYNC_DATABASE_URL = (
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset=utf8mb4"
)

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=15,
    max_overflow=25,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_use_lifo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

class Base(DeclarativeBase): # 必须使用同一个Base对象表之间才能相互加载
    """
        所有模型必须继承此基类，以确保它们共享同一个 MetaData 注册表。
        只有在同一个注册表下，模型间的外键引用（如 ForeignKey）才能被正确解析。
        """
    pass