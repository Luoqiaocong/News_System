# Utils/LogUtil.py
import os
import sys
from loguru import logger
from Config.LogConfig import settings

def init_log():
    # 移除默认处理器
    logger.remove()

    # 1. 配置控制台输出
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # 2. 配置输出到文件
    if settings.LOG_TO_FILE:
        # 获取项目根目录下的 logs 文件夹
        log_dir = os.path.join(os.getcwd(), settings.LOG_SAVE_PATH)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logger.add(
            os.path.join(log_dir, "news_system.log"),
            rotation="10 MB",
            retention="7 days",
            level=settings.LOG_LEVEL,
            encoding="utf-8",
            enqueue=True  # 异步写入
        )

# 统一暴露 logger 供其他模块导入
log = logger