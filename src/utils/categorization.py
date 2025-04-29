"""
Account categorization system for profit and loss reports.

This module provides functionality to categorize financial accounts based on
account names and codes, grouping them into meaningful business categories.
"""

from typing import Dict, List, Any, Optional, Union
import re
import logging

# Import the application logger
from src.utils.logger import app_logger

# Configure module-specific logger
logger = app_logger.getChild('categorization')


# Define category mapping based on common account names and patterns
ACCOUNT_CATEGORIES = {
    # Revenue/Income categories
    "sales": "Sales",
    "revenue": "Sales",
    "income": "Sales",
    "service": "Service Revenue",
    "commission": "Commission Income",
    "interest": "Interest Income",
    "discount": "Discounts",
    "rebate": "Rebates",
    
    # Cost of Sales categories
    "cost of sales": "Direct Costs",
    "cost of goods sold": "Direct Costs",
    "cogs": "Direct Costs",
    "direct cost": "Direct Costs",
    "material": "Materials",
    "inventory": "Inventory",
    "freight": "Freight & Shipping",
    "shipping": "Freight & Shipping",
    "production": "Production",
    "labor": "Labor",
    
    # Operating Expense categories
    "salary": "Salaries & Wages",
    "wage": "Salaries & Wages",
    "payroll": "Salaries & Wages",
    "benefit": "Employee Benefits",
    "insurance": "Insurance",
    "rent": "Rent & Lease",
    "lease": "Rent & Lease",
    "utility": "Utilities",
    "electric": "Utilities",
    "water": "Utilities",
    "gas": "Utilities",
    "phone": "Telecommunications",
    "internet": "Telecommunications",
    "telecom": "Telecommunications",
    "office": "Office Expenses",
    "supplies": "Office Supplies",
    "equipment": "Equipment",
    "repair": "Repairs & Maintenance",
    "maintenance": "Repairs & Maintenance",
    "travel": "Travel",
    "meal": "Meals & Entertainment",
    "entertainment": "Meals & Entertainment",
    "marketing": "Marketing",
    "advertising": "Advertising",
    "promotion": "Promotions",
    "professional": "Professional Services",
    "legal": "Legal",
    "accounting": "Accounting",
    "consulting": "Consulting",
    "bank": "Bank Charges",
    "fee": "Fees",
    "tax": "Taxes",
    "depreciation": "Depreciation",
    "amortization": "Amortization",
    "interest expense": "Interest Expense",
    "bad debt": "Bad Debt",
    "donation": "Donations",
    "subscription": "Subscriptions",
    "software": "Software",
    "training": "Training & Development",
    "research": "Research & Development",
    "r&d": "Research & Development",
    "miscellaneous": "Miscellaneous",
    "other": "Other"
}

# Account code ranges for specific categories (if available)
# Format: (start_code, end_code): category
CODE_RANGES = {
    # Example ranges - these should be customized based on the chart of accounts
    (1000, 1999): "Assets",
    (2000, 2999): "Liabilities",
    (3000, 3999): "Equity",
    (4000, 4999): "Revenue",
    (5000, 5999): "Cost of Sales",
    (6000, 9999): "Expenses"
}

# Section-specific category mappings
SECTION_CATEGORIES = {
    "tradingIncome": {
        "default": "Sales",
        # Additional section-specific mappings
        "discount": "Sales Discounts",
        "return": "Sales Returns"
    },
    "costOfSales": {
        "default": "Direct Costs",
        # Additional section-specific mappings
    },
    "operatingExpenses": {
        "default": "Other Expenses",
        # Additional section-specific mappings
    }
}


def categorize_account(account: Dict[str, Any], section: str) -> str:
    """
    Categorize an account based on its name, code, and section.
    
    Args:
        account: The account dictionary containing name and optionally code.
        section: The section this account belongs to.
        
    Returns:
        The category string for the account.
    """
    account_name = account.get('name', '').lower()
    account_code = account.get('code')
    
    logger.debug(f"Categorizing account: {account_name}, code: {account_code}, section: {section}")
    
    # Try to categorize by account code if available
    if account_code:
        try:
            # Ensure account_code is a string before attempting conversion
            if isinstance(account_code, str):
                # Remove any non-numeric characters
                clean_code = re.sub(r'[^0-9]', '', account_code)
                if clean_code:
                    code_num = int(clean_code)
                    logger.debug(f"Checking code ranges for code: {code_num}")
                    for (start, end), category in CODE_RANGES.items():
                        if start <= code_num <= end:
                            logger.info(f"Categorized '{account_name}' as '{category}' based on code {code_num}")
                            return category
            else:
                logger.warning(f"Account code is not a string: {type(account_code)}, value: {account_code}")
        except (ValueError, TypeError) as e:
            # If code is not a valid integer, log the error and continue with name-based categorization
            logger.warning(f"Error processing account code '{account_code}': {str(e)}")
    
    # Check for section-specific categories
    section_mapping = SECTION_CATEGORIES.get(section, {})
    logger.debug(f"Using section mapping for {section}")
    
    # Try to find a match in the account name
    for keyword, category in ACCOUNT_CATEGORIES.items():
        if keyword in account_name:
            # Check if there's a section-specific override for this keyword
            if keyword in section_mapping:
                result = section_mapping[keyword]
                logger.info(f"Categorized '{account_name}' as '{result}' based on section-specific keyword '{keyword}'")
                return result
            
            logger.info(f"Categorized '{account_name}' as '{category}' based on keyword '{keyword}'")
            return category
    
    # If no match found, return the default category for the section
    default_category = section_mapping.get('default', 'Uncategorized')
    logger.info(f"Using default category '{default_category}' for '{account_name}' in section '{section}'")
    return default_category


def add_categories_to_accounts(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add category field to all accounts in the profit and loss data.
    
    Args:
        data: The profit and loss data dictionary.
        
    Returns:
        Updated profit and loss data with categories added to accounts.
    """
    # Create a deep copy to avoid modifying the original
    result = data.copy()
    sections = result.get('sections', {})
    
    logger.info(f"Adding categories to accounts in {len(sections)} sections")
    
    # Process each section with accounts
    for section_name, section_data in sections.items():
        if isinstance(section_data, dict) and 'accounts' in section_data:
            account_count = len(section_data['accounts'])
            logger.info(f"Processing {account_count} accounts in section '{section_name}'")
            
            for i, account in enumerate(section_data['accounts']):
                try:
                    # Add category to the account
                    account['category'] = categorize_account(account, section_name)
                except Exception as e:
                    # Log error but continue processing other accounts
                    logger.error(f"Error categorizing account {i} in section '{section_name}': {str(e)}")
                    logger.error(f"Account data: {account}")
                    # Set a default category to avoid further errors
                    account['category'] = 'Uncategorized'
    
    logger.info("Finished adding categories to all accounts")
    return result


def get_accounts_by_category(data: Dict[str, Any], section: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group accounts by their categories.
    
    Args:
        data: The profit and loss data dictionary with categorized accounts.
        section: Optional section name to filter accounts.
        
    Returns:
        Dictionary with categories as keys and lists of accounts as values.
    """
    categorized = {}
    sections = data.get('sections', {})
    
    # Process specified section or all sections
    section_items = [(section, sections.get(section, {}))] if section else sections.items()
    
    logger.debug(f"Grouping accounts by category" + (f" in section '{section}'" if section else ""))
    
    for section_name, section_data in section_items:
        if isinstance(section_data, dict) and 'accounts' in section_data:
            account_count = len(section_data['accounts'])
            logger.debug(f"Processing {account_count} accounts in section '{section_name}'")
            
            for account in section_data['accounts']:
                try:
                    # Get category, defaulting to 'Uncategorized' if not present
                    category = account.get('category', 'Uncategorized')
                    
                    if category not in categorized:
                        categorized[category] = []
                    
                    # Add account with section information
                    account_copy = account.copy()
                    account_copy['section'] = section_name
                    categorized[category].append(account_copy)
                except Exception as e:
                    logger.error(f"Error processing account {account.get('name', 'unknown')} in section '{section_name}': {str(e)}")
    
    logger.debug(f"Grouped accounts into {len(categorized)} categories")
    return categorized


def get_category_totals(data: Dict[str, Any], section: Optional[str] = None) -> Dict[str, float]:
    """
    Calculate total values for each category.
    
    Args:
        data: The profit and loss data dictionary with categorized accounts.
        section: Optional section name to filter accounts.
        
    Returns:
        Dictionary with categories as keys and total values as values.
    """
    categorized = get_accounts_by_category(data, section)
    totals = {}
    
    logger.debug(f"Calculating totals for {len(categorized)} categories" + 
                (f" in section '{section}'" if section else ""))
    
    for category, accounts in categorized.items():
        try:
            # Sum all account values in this category
            category_total = sum(account.get('value', 0) for account in accounts)
            totals[category] = category_total
            logger.debug(f"Category '{category}' total: {category_total:.2f}")
        except Exception as e:
            logger.error(f"Error calculating total for category '{category}': {str(e)}")
            # Set a default value to avoid further errors
            totals[category] = 0.0
    
    return totals
