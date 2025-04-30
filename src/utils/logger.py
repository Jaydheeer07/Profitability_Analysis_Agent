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

# Create logs directory if it doesn't exist
app_dir = Path(__file__).parent.parent.parent
logs_dir = app_dir / "logs"

if not logs_dir.exists():
    logs_dir.mkdir(exist_ok=True)

# Create log file with timestamp
timestamp = datetime.now().strftime("%Y%m%d")
log_file = logs_dir / f"profitability_analyzer_{timestamp}.log"

# Create formatter for consistent log format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure root logger to capture all logs
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Clear existing handlers to avoid duplicates
if root_logger.handlers:
    root_logger.handlers.clear()

# Add console handler to root logger
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Add file handler to root logger
file_handler = logging.FileHandler(str(log_file))
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# Create application logger as a child of root logger
app_logger = logging.getLogger("profitability_analyzer")
app_logger.setLevel(logging.INFO)
# No need to add handlers to app_logger as it will use root logger's handlers

def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        module_name: Name of the module.
        
    Returns:
        Logger instance for the module.
    """
    logger_name = f"profitability_analyzer.{module_name}"
    return logging.getLogger(logger_name)


# app_logger is already defined above
