from loguru import logger
from app.config import settings

def setup_logging() -> 'loguru.Logger':
    """Configure and return the Loguru logger."""
    logger.remove()
    logger.add(
        "logs/app.log",
        rotation="1 week",
        retention="4 weeks",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    return logger

logger = setup_logging()
