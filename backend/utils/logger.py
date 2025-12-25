import logging
import sys
from backend.config.settings import settings


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name: Name of the logger
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level from settings if not provided
    if level is None:
        level = settings.LOG_LEVEL

    logger.setLevel(getattr(logging, level.upper()))

    # Prevent adding multiple handlers if logger already has handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger