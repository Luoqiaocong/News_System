import sys
from pathlib import Path
from loguru import logger
from Config.LogConfig import settings

def init_log():
    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    if settings.LOG_TO_FILE:
        log_dir = Path(__file__).parent.parent / settings.LOG_SAVE_PATH
        log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_dir / "news_system.log",
            rotation="10 MB",
            retention="7 days",
            level=settings.LOG_LEVEL,
            encoding="utf-8",
            enqueue=True
        )

log = logger