"""
Logging configuration for the budget application.
"""
import logging
from logging.handlers import RotatingFileHandler
import sys
import os
import traceback

# Update import to use configs
from configs.logging_config import LOGGER

def setup_logger(name='budget'):
    """
    Set up and configure the application logger.
    
    Args:
        name (str): The name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level from config
    level = getattr(logging, LOGGER['level'].upper(), logging.INFO)
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Enhanced formatter to include file path and line number
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Create file handler
    try:
        # Ensure the log directory exists
        log_file = LOGGER['file']
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOGGER['max_size'],
            backupCount=LOGGER['backup_count']
        )
        file_handler.setLevel(level)
        
        # Use the same enhanced formatter for file logging
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    except Exception as e:
        # Fallback to console-only logging if file logging fails
        print(f"Warning: Could not set up file logging. Error: {e}")
        logger.addHandler(console_handler)
    
    logger.info(f"Logger initialized with level {LOGGER['level']}")
    
    return logger

def log_exception(logger, message="An error occurred"):
    """
    Log an exception with full traceback details.
    
    Args:
        logger (logging.Logger): Logger to use
        message (str, optional): Custom error message
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    
    # Log the full traceback
    logger.error(message)
    for line in lines:
        logger.error(line.strip())

# Create the main application logger
logger = setup_logger()