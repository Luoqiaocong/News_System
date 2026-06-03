from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Session, with_loader_criteria
from Config.settings import settings


# ==================== 数据库配置 ====================
ASYNC_DATABASE_URL = (
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset=utf8mb4"
)
# 连接池配置
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


# 🌟 1. event.listens_for：这是 SQLAlchemy 的全局“物理外挂监听器”
# 它告诉系统：只要有任何一个 AsyncSession 准备向 MySQL 发射 ORM 执行语句（"do_orm_execute"），
# 在发射前的微秒级瞬间，立刻强行刹车，把这条语句丢进这个 _add_soft_delete_filter 函数里进行体检和改装！
@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_filter(execute_state):
    from models.User import User
    
    # 🌟 2. 检查本次查询有没有开启“阳间穿透特权”
    # 当你在登录或注册 Service 里写了 .execution_options(include_deleted=True) 时，
    # execute_state.execution_options 字典里就会抓到这个信号。
    include_deleted = execute_state.execution_options.get("include_deleted", False)
    
    if include_deleted:
        # 如果带有穿透特权，天网立刻抬起闸门放行，绝对不污染原本的 SQL 语句，
        # 这样登录接口就能顺利从“停尸房”里把注销的老用户捞出来验证密码或触发复活。
        return

    # 🌟 3. 规避系统内部的“细碎子查询” I/O 干扰
    # is_column_load: 是否是延迟加载某一个列（比如大文本 deferred 加载）
    # is_relationship_load: 是否是 ORM 正在自动加载关联表（比如加载 User 关联的 Profile）
    # 我们只拦截主干的大型业务 `SELECT` 查询，如果是系统内部自动衍生的小动作，则放行，防止引发死锁或内耗。
    if not execute_state.is_column_load and not execute_state.is_relationship_load:
        
        # 🌟 4. 天网的核心物理改装动作：重写 SQL 语句
        # with_loader_criteria：这是 SQLAlchemy 2.0 最顶级的“元编程全局过滤器”工具。
        # 它会在当前即将发射的 SQL 语句末尾，原子化地横空插入一段条件。
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(User, User.deleted_at == None, include_aliases=True)
        )