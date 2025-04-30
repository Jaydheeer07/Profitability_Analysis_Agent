"""
Common utility functions for the Profitability Analysis Agent.

This module provides helper functions that are used across
different parts of the application.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Import centralized logger
from src.utils.logger import app_logger as logger


def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Dictionary data to save.
        file_path: Path to save the JSON file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file: {str(e)}")
        return False


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dictionary containing the loaded data, or None if an error occurred.
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {str(e)}")
        return None


def get_timestamp() -> str:
    """
    Get the current timestamp as a formatted string.
    
    Returns:
        Formatted timestamp string.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_currency(value: float, currency_symbol: str = "$") -> str:
    """
    Format a numeric value as currency.
    
    Args:
        value: Numeric value to format.
        currency_symbol: Currency symbol to use.
        
    Returns:
        Formatted currency string.
    """
    return f"{currency_symbol}{abs(value):,.2f}"


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage safely (handling division by zero).
    
    Args:
        part: The part value.
        total: The total value.
        
    Returns:
        Calculated percentage or 0 if total is 0.
    """
    if total == 0:
        return 0
    return (part / total) * 100