"""
Logging utility for the Profitability Analysis Agent.

This module provides a centralized logging system for the application,
allowing consistent logging across all components.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "profitability_analyzer",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name: Name of the logger.
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Path to log file. If None, logs will only be sent to console.
        console_output: Whether to output logs to console.
        
    Returns:
        Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default application logger
def get_app_logger() -> logging.Logger:
    """
    Get the application-wide logger.
    
    Returns:
        Application logger instance.
    """
    # Create logs directory if it doesn't exist
    app_dir = Path(__file__).parent.parent.parent
    logs_dir = app_dir / "logs"
    
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = logs_dir / f"profitability_analyzer_{timestamp}.log"
    
    return setup_logger(
        name="profitability_analyzer",
        log_level=logging.INFO,
        log_file=str(log_file),
        console_output=True
    )


# Singleton logger instance for the application
app_logger = get_app_logger()
