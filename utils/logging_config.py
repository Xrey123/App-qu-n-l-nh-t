"""
Logging Configuration for ShopFlow Application

Usage:
    from utils.logging_config import get_logger
    
    logger = get_logger(__name__)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message", exc_info=True)
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Logging levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Default log directory
LOG_DIR = "logs"

# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Global logging configuration
_configured = False


def configure_logging(level=INFO, log_to_file=True, log_to_console=True):
    """
    Configure global logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to file
        log_to_console: Whether to print logs to console
    """
    global _configured
    
    if _configured:
        return
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Format: [2025-11-08 10:30:45] [INFO] [main_gui] Message
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (only show WARNING and above in production)
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(WARNING if level <= INFO else level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (rotating, max 10MB per file, keep 5 backups)
    if log_to_file:
        log_file = os.path.join(LOG_DIR, f"shopflow_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(DEBUG)  # Log everything to file
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _configured = True


def get_logger(name):
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.debug("Debug info")
        logger.error("Error occurred", exc_info=True)
    """
    # Auto-configure if not already done
    if not _configured:
        # In production: INFO level, in development: DEBUG level
        # You can change this based on environment variable
        level = DEBUG if os.getenv('DEBUG', '').lower() == 'true' else INFO
        configure_logging(level=level)
    
    return logging.getLogger(name)


def log_exception(logger, message="Exception occurred"):
    """
    Helper to log exception with full traceback.
    
    Args:
        logger: Logger instance
        message: Custom message to prepend
    
    Example:
        try:
            risky_operation()
        except Exception as e:
            log_exception(logger, f"Failed to do risky operation: {e}")
    """
    logger.error(message, exc_info=True)


# Convenience function for one-off debug logging
def debug_print(*args, **kwargs):
    """
    Temporary debug print that goes to logger.
    Use this to replace print() statements during refactoring.
    
    Example:
        debug_print("Value:", value, "Status:", status)
    """
    logger = get_logger("debug")
    message = " ".join(str(arg) for arg in args)
    logger.debug(message)
