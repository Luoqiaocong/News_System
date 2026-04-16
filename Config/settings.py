from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker

# ==================== 数据库配置 ====================
ASYNC_DATABASE_URL = "mysql+aiomysql://root:root@localhost:3306/mynews?charset=utf8mb4"

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,                    # 生产关闭
    future=True,                   # 使用 2.0 风格
    pool_size=15,                  # 根据实际并发调整
    max_overflow=25,
    pool_timeout=30,
    pool_pre_ping=True,            # 防僵尸连接
    pool_recycle=3600,             # 每小时回收一次
    pool_use_lifo=True,            # 可选优化
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # 强烈推荐
    autoflush=False,               # 推荐关闭
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()