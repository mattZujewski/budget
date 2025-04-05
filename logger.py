"""
Logging configuration for the budget application.
"""
import logging
from logging.handlers import RotatingFileHandler
import sys
from .config import LOGGER

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
    console_formatter = logging.Formatter(LOGGER['format'])
    console_handler.setFormatter(console_formatter)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        LOGGER['file'],
        maxBytes=LOGGER['max_size'],
        backupCount=LOGGER['backup_count']
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOGGER['format'])
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logger initialized with level {LOGGER['level']}")
    
    return logger

# Create the main application logger
logger = setup_logger()