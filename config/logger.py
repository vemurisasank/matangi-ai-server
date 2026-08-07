from loguru import logger
import sys

from config.settings import settings


logger.remove()

logger.add(

    sys.stdout,

    level=settings.LOG_LEVEL,

    colorize=True,

    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>"

)

logger.add(

    "logs/server.log",

    rotation="10 MB",

    retention="30 days",

    level=settings.LOG_LEVEL

)