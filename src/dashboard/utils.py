"""
Utility functions for the Profitability Analysis Dashboard.

This module contains helper functions for data processing, financial calculations,
and visualization utilities used by the Streamlit dashboard.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from src.core.ratios import calculate_financial_metrics


def calculate_financial_ratios(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate key financial ratios from profit and loss data.
    
    Args:
        data: The profit and loss data dictionary.
        
    Returns:
        Dictionary containing calculated financial ratios.
    """
    # Use the new comprehensive metrics calculation function from ratios.py
    metrics = calculate_financial_metrics(data)
    
    # For backward compatibility, map the new metric names to the old ones
    # and ensure all expected keys are present
    ratios = {
        'gross_margin': metrics.get('gross_margin', 0),
        'net_margin': metrics.get('net_margin', 0),
        'expense_ratio': metrics.get('expense_ratio', 0),
        'cogs_ratio': metrics.get('cogs_ratio', 0),
        'operating_profit_margin': metrics.get('operating_margin', 0)
    }
    
    return ratios


def get_top_accounts(data: Dict[str, Any], section: str, n: int = 10) -> pd.DataFrame:
    """
    Get the top N accounts by absolute value from a specific section.
    
    Args:
        data: The profit and loss data dictionary.
        section: The section to extract accounts from.
        n: Number of top accounts to return.
        
    Returns:
        DataFrame containing the top accounts.
    """
    sections = data.get('sections', {})
    
    if section in sections and 'accounts' in sections[section]:
        accounts = sections[section]['accounts']
        
        # Convert to DataFrame
        df = pd.DataFrame(accounts)
        
        if not df.empty:
            # Sort by absolute value
            df['abs_value'] = df['value'].abs()
            df = df.sort_values('abs_value', ascending=False).head(n)
            df = df.drop('abs_value', axis=1)
            
            return df
    
    return pd.DataFrame()


def format_currency(value: Union[int, float]) -> str:
    """
    Format a numeric value as currency.
    
    Args:
        value: Numeric value to format.
        
    Returns:
        Formatted currency string.
    """
    return f"${value:,.2f}"


def get_section_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of all sections in the profit and loss data.
    
    Args:
        data: The profit and loss data dictionary.
        
    Returns:
        Dictionary with section summaries.
    """
    sections = data.get('sections', {})
    summary = {}
    
    # Extract key metrics
    if 'tradingIncome' in sections:
        summary['trading_income'] = sections['tradingIncome'].get('total', 0)
        summary['income_accounts_count'] = len(sections['tradingIncome'].get('accounts', []))
    
    if 'costOfSales' in sections:
        summary['cost_of_sales'] = sections['costOfSales'].get('total', 0)
        summary['cogs_accounts_count'] = len(sections['costOfSales'].get('accounts', []))
    
    if 'grossProfit' in sections:
        summary['gross_profit'] = sections['grossProfit']
    
    if 'operatingExpenses' in sections:
        summary['operating_expenses'] = sections['operatingExpenses'].get('total', 0)
        summary['expense_accounts_count'] = len(sections['operatingExpenses'].get('accounts', []))
    
    if 'netProfit' in sections:
        summary['net_profit'] = sections['netProfit']
    
    return summary


def create_accounts_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a consolidated DataFrame of all accounts with their sections.
    
    Args:
        data: The profit and loss data dictionary.
        
    Returns:
        DataFrame containing all accounts with section information.
    """
    all_accounts = []
    sections = data.get('sections', {})
    
    for section_name, section_data in sections.items():
        if isinstance(section_data, dict) and 'accounts' in section_data:
            for account in section_data['accounts']:
                account_copy = account.copy()
                account_copy['section'] = section_name
                all_accounts.append(account_copy)
    
    if all_accounts:
        return pd.DataFrame(all_accounts)
    
    return pd.DataFrame()