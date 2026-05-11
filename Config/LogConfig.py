class LogConfig:
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True  # 是否输出到文件
    LOG_SAVE_PATH: str = "logs"  # 日志存放文件夹名

settings: LogConfig = LogConfig()