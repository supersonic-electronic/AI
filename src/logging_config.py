"""
Centralized logging configuration for the portfolio optimizer project.

This module provides a structured logging setup using logging.config.dictConfig()
with support for file and console handlers, custom formatters, and module-specific loggers.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.settings import Settings


def get_logging_config(settings: Settings) -> Dict[str, Any]:
    """
    Generate logging configuration dictionary based on settings.
    
    Args:
        settings: Application settings instance
        
    Returns:
        Logging configuration dictionary for logging.config.dictConfig()
    """
    # Ensure log directory exists
    log_dir = settings.log_file.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            },
            "json": {
                "class": "logging.Formatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(lineno)d %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "console_error": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "stream": "ext://sys.stderr"
            }
        },
        "loggers": {
            # Root logger
            "": {
                "level": settings.log_level,
                "handlers": ["console"]
            },
            # Package-specific loggers
            "src": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "src.ingestion": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "src.ingestion.pdf2txt": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "src.ingestion.chunk_embed": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            # Third-party library loggers
            "openai": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "pinecone": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "chromadb": {
                "level": "WARNING", 
                "handlers": ["console"],
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "requests": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if file logging is enabled
    if settings.log_to_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "filename": str(settings.log_file),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            if "file" not in logger_config["handlers"]:
                logger_config["handlers"].append("file")
        
        # Add error file handler for critical errors
        config["handlers"]["error_file"] = {
            "class": "logging.FileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": str(settings.log_file.parent / "errors.log"),
            "encoding": "utf-8"
        }
        
        # Add error file handler to root logger
        config["loggers"][""]["handlers"].append("error_file")
    
    return config


def setup_logging(settings: Settings, force_reload: bool = False) -> None:
    """
    Setup logging configuration using dictConfig.
    
    Args:
        settings: Application settings instance
        force_reload: Whether to force reload of logging configuration
    """
    # Check if logging is already configured
    if not force_reload and logging.getLogger().handlers:
        return
    
    # Get logging configuration
    config = get_logging_config(settings)
    
    # Apply configuration
    try:
        logging.config.dictConfig(config)
        
        # Configure third-party loggers after setup
        configure_third_party_loggers()
        
        # Log system information in debug mode
        root_logger = logging.getLogger()
        if root_logger.getEffectiveLevel() == logging.DEBUG:
            log_system_info(root_logger)
            
    except Exception as e:
        # Fallback to basic configuration if dictConfig fails
        logging.basicConfig(
            level=getattr(logging, settings.log_level),
            format=settings.log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(settings.log_file) if settings.log_to_file else logging.NullHandler()
            ]
        )
        logging.error(f"Failed to setup structured logging, using basic config: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: Union[str, int], logger_name: Optional[str] = None) -> None:
    """
    Dynamically change log level for a specific logger or all loggers.
    
    Args:
        level: Log level (string or logging constant)
        logger_name: Specific logger name, or None for root logger
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    if logger_name:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    else:
        logging.getLogger().setLevel(level)


def log_system_info(logger: logging.Logger) -> None:
    """
    Log system information for debugging purposes.
    
    Args:
        logger: Logger instance to use
    """
    import os
    import platform
    import sys
    from pathlib import Path
    
    logger.info("System Information:")
    logger.info(f"  Python version: {sys.version}")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Working directory: {Path.cwd()}")
    logger.info(f"  Process ID: {os.getpid()}")


def create_performance_logger(name: str = "performance") -> logging.Logger:
    """
    Create a specialized logger for performance monitoring.
    
    Args:
        name: Logger name
        
    Returns:
        Performance logger instance
    """
    logger = logging.getLogger(name)
    
    # Create a separate handler for performance logs
    handler = logging.FileHandler("logs/performance.log")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger


class LoggingContext:
    """Context manager for temporary logging configuration changes."""
    
    def __init__(self, logger_name: str, level: Union[str, int], add_handler: Optional[logging.Handler] = None):
        """
        Initialize logging context.
        
        Args:
            logger_name: Name of logger to modify
            level: Temporary log level
            add_handler: Optional handler to add temporarily
        """
        self.logger_name = logger_name
        self.new_level = level if isinstance(level, int) else getattr(logging, level.upper())
        self.add_handler = add_handler
        self.original_level = None
        self.handler_added = False
    
    def __enter__(self) -> logging.Logger:
        """Enter the context and apply temporary configuration."""
        logger = logging.getLogger(self.logger_name)
        self.original_level = logger.level
        logger.setLevel(self.new_level)
        
        if self.add_handler:
            logger.addHandler(self.add_handler)
            self.handler_added = True
        
        return logger
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context and restore original configuration."""
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.original_level)
        
        if self.handler_added and self.add_handler:
            logger.removeHandler(self.add_handler)


def configure_third_party_loggers() -> None:
    """Configure third-party library loggers to reduce noise."""
    # Reduce verbosity of common third-party libraries
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("requests.packages.urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)


# Global performance logger
performance_logger = None


def get_performance_logger() -> logging.Logger:
    """Get the global performance logger instance."""
    global performance_logger
    if performance_logger is None:
        performance_logger = create_performance_logger()
    return performance_logger


def time_function(func_name: str):
    """
    Decorator to log function execution time.
    
    Args:
        func_name: Name to use in log messages
    """
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_performance_logger()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func_name} completed in {execution_time:.3f} seconds")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func_name} failed after {execution_time:.3f} seconds: {e}")
                raise
        
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Create a test settings instance
    class TestSettings:
        log_level = "DEBUG"
        log_to_file = True
        log_file = Path("logs/test.log")
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    settings = TestSettings()
    
    # Setup logging
    setup_logging(settings)
    
    # Test different loggers
    root_logger = get_logger(__name__)
    ingestion_logger = get_logger("src.ingestion.pdf2txt")
    
    # Test logging at different levels
    root_logger.debug("Debug message from root logger")
    root_logger.info("Info message from root logger")
    root_logger.warning("Warning message from root logger")
    root_logger.error("Error message from root logger")
    
    ingestion_logger.info("Info message from ingestion logger")
    
    # Test performance logging
    @time_function("test_operation")
    def test_operation():
        import time
        time.sleep(0.1)
        return "completed"
    
    result = test_operation()
    print(f"Operation result: {result}")
    
    # Test logging context
    with LoggingContext("src.ingestion", "DEBUG") as logger:
        logger.debug("Debug message in context")
    
    print("Logging configuration test completed")