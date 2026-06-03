# Tasks/cleanup_task.py
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import delete

from Utils.LogUtil import log
from Config.DataBaseConfig import AsyncSessionLocal  
from models.User import User           

# 实例化全局的异步调度器
scheduler = AsyncIOScheduler()

async def _physical_cleanup_expired_users():
    """内部函数：真正的异步物理删除逻辑"""
    log.info("开始巡检数据库...")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            boundary_dt = datetime.now() - timedelta(minutes=10)
            boundary_time = boundary_dt.strftime("%Y-%m-%d %H:%M:%S")

            delete_stmt = delete(User).where(User.deleted_at < boundary_time)\
                .execution_options(include_deleted=True)  # 穿透全局过滤器
            log.info(str(delete_stmt.compile(compile_kwargs={"literal_binds": True})))
            result = await session.execute(delete_stmt)
            affected_rows = result.rowcount # type: ignore
            await session.commit()
            
    if affected_rows > 0:
        log.info(f"[定时任务] 物理清理成功！已从 MySQL 彻底粉碎 {affected_rows} 个到期账户。")
    else:
        log.info("[定时任务] 巡检结束，未发现满足条件的过期账户。")


def start_expired_user_cleanup():
    """外部函数：供 main.py 调用的启动接口"""
    # 🌟 本地测试：每分钟跑一次
    # scheduler.add_job(_physical_cleanup_expired_users, 'interval', minutes=1)
    
    # 🌟 生产环境：每天凌晨 3 点跑一次
    scheduler.add_job(_physical_cleanup_expired_users, 'cron', hour=3, minute=0)
    
    scheduler.start()
    log.info("🚀 后台异步定时任务 [AsyncIOScheduler] 已在独立子模块中成功启动！")


def stop_expired_user_cleanup():
    """外部函数：供 main.py 调用的关闭接口"""
    scheduler.shutdown()
    log.info("🛑 后台定时任务调度器已优雅安全关闭。")