import sys
from loguru import logger
from core.config_data import settings
import os
# 移除默认的处理器
logger.remove()

# 1. 输出到控制台 (Console)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 2. 输出到文件 (File) - 每天生成一个新文件，保留7天
log_path = os.path.join(settings.DATA_DIR, "logs", "fitness_ai.log")
logger.add(
    log_path,
    rotation="00:00", # 每天零点分割
    retention="7 days", # 保留7天
    compression="zip", # 压缩历史日志
    encoding="utf-8",
    level="DEBUG"
)

# 导出配置好的 logger
__all__ = ["logger"] #是一种声明——“这个文件虽然写了很多代码，但对外提供的服务只有一个，就是 logger 对象。”