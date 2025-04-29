"""
Core profit and loss analysis functionality.

This module provides functions for analyzing profit and loss Excel reports
and extracting structured financial data.
"""

import pandas as pd
import json
import os
import re
from datetime import datetime


def extract_company_and_period(df):
    """
    Extract company name and period from the Excel file.
    
    Args:
        df (pandas.DataFrame): The dataframe containing the P&L data.
        
    Returns:
        tuple: (company_name, period) strings.
    """
    # Try to find company name in the first few rows
    company_name = None
    period = None
    
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        row_str = ' '.join(str(x) for x in row if pd.notna(x))
        
        # Look for company name (usually in the first rows)
        if company_name is None and row_str and not row_str.lower().startswith(('profit', 'loss', 'p&l', 'income')):
            company_name = row_str
        
        # Look for period indicators
        period_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}|for\s+the\s+\w+\s+ended\s+[\w\s,]+\d{4}|year\s+to\s+date\s+[\w\s,]+\d{4}', 
                               row_str.lower())
        if period_match:
            period = period_match.group(0).title()
            break
    
    return company_name, period


def identify_basis_type(df):
    """
    Identify if the report is on Accrual or Cash basis.
    
    Args:
        df (pandas.DataFrame): The dataframe containing the P&L data.
        
    Returns:
        str: 'Accrual' or 'Cash'.
    """
    for i in range(min(15, len(df))):
        row = df.iloc[i]
        row_str = ' '.join(str(x) for x in row if pd.notna(x)).lower()
        if 'accrual basis' in row_str:
            return 'Accrual'
        elif 'cash basis' in row_str:
            return 'Cash'
    
    # Default to Accrual if not specified
    return 'Accrual'


def find_section_boundaries(df):
    """
    Find the row indices for each section of the profit and loss report.
    
    Args:
        df (pandas.DataFrame): The dataframe containing the P&L data.
        
    Returns:
        dict: Dictionary with section boundaries.
    """
    sections = {
        'tradingIncome': {'start': None, 'end': None},
        'costOfSales': {'start': None, 'end': None},
        'grossProfit': {'row': None},
        'operatingExpenses': {'start': None, 'end': None},
        'netProfit': {'row': None}
    }
    
    # Keywords to identify each section
    section_keywords = {
        'tradingIncome': ['trading income', 'revenue', 'sales', 'income', 'operating revenue'],
        'costOfSales': ['cost of sales', 'cost of goods sold', 'cogs', 'direct costs'],
        'grossProfit': ['gross profit', 'gross income', 'gross margin'],
        'operatingExpenses': ['operating expenses', 'expenses', 'overhead', 'indirect costs', 'administrative expenses'],
        'netProfit': ['net profit', 'net income', 'profit for the period', 'net earnings', 'net operating profit']
    }
    
    # Find the start and end rows for each section
    for i in range(len(df)):
        row = df.iloc[i]
        row_str = ' '.join(str(x) for x in row if pd.notna(x)).lower()
        
        # Check for section headers
        for section, keywords in section_keywords.items():
            if any(keyword in row_str for keyword in keywords):
                if section in ['tradingIncome', 'costOfSales', 'operatingExpenses']:
                    if sections[section]['start'] is None:
                        sections[section]['start'] = i
                elif section in ['grossProfit', 'netProfit']:
                    sections[section]['row'] = i
    
    # Determine end rows for sections
    for section in ['tradingIncome', 'costOfSales', 'operatingExpenses']:
        if sections[section]['start'] is not None:
            # Find the next section start after this one
            next_section_start = len(df)
            for other_section in sections:
                if other_section != section:
                    if 'start' in sections[other_section] and sections[other_section]['start'] is not None:
                        if sections[other_section]['start'] > sections[section]['start'] and sections[other_section]['start'] < next_section_start:
                            next_section_start = sections[other_section]['start']
                    elif 'row' in sections[other_section] and sections[other_section]['row'] is not None:
                        if sections[other_section]['row'] > sections[section]['start'] and sections[other_section]['row'] < next_section_start:
                            next_section_start = sections[other_section]['row']
            
            # Set the end row (one row before the next section)
            if next_section_start < len(df):
                sections[section]['end'] = next_section_start - 1
            else:
                # If no next section, use a reasonable number of rows
                sections[section]['end'] = min(sections[section]['start'] + 20, len(df) - 1)
    
    return sections


def extract_accounts(df, start_row, end_row):
    """
    Extract account details from a section of the profit and loss report.
    
    Args:
        df (pandas.DataFrame): The dataframe containing the P&L data.
        start_row (int): Starting row index.
        end_row (int): Ending row index.
        
    Returns:
        tuple: (accounts_list, total_value).
    """
    accounts = []
    total_value = None
    
    # Skip the header row
    start_row += 1
    
    for i in range(start_row, end_row + 1):
        row = df.iloc[i]
        
        # Skip empty rows
        if all(pd.isna(x) for x in row):
            continue
        
        # Convert row to string for easier processing
        row_str = ' '.join(str(x) for x in row if pd.notna(x)).lower()
        
        # Skip rows that are likely headers or subtotals
        if any(keyword in row_str for keyword in ['total', 'subtotal']):
            # This might be the total row, try to extract the total value
            for j in range(len(row) - 1, -1, -1):
                if pd.notna(row.iloc[j]) and (isinstance(row.iloc[j], (int, float)) or 
                                             (isinstance(row.iloc[j], str) and row.iloc[j].replace('.', '', 1).replace('-', '', 1).isdigit())):
                    try:
                        total_value = float(row.iloc[j])
                        break
                    except (ValueError, TypeError):
                        pass
            continue
        
        # Extract account details
        account_name = None
        account_code = None
        account_value = None
        
        # Find account name (usually in the first few columns)
        for j in range(min(3, len(row))):
            if pd.notna(row.iloc[j]) and isinstance(row.iloc[j], str) and len(row.iloc[j].strip()) > 0:
                account_name = row.iloc[j].strip()
                break
        
        # Find account code (usually a numeric code near the name)
        for j in range(min(3, len(row))):
            if pd.notna(row.iloc[j]) and isinstance(row.iloc[j], str) and re.match(r'^\d+$', row.iloc[j].strip()):
                account_code = row.iloc[j].strip()
                break
        
        # Find account value (usually in the last few columns)
        for j in range(len(row) - 1, max(0, len(row) - 4), -1):
            if pd.notna(row.iloc[j]) and (isinstance(row.iloc[j], (int, float)) or 
                                         (isinstance(row.iloc[j], str) and row.iloc[j].replace('.', '', 1).replace('-', '', 1).isdigit())):
                try:
                    account_value = float(row.iloc[j])
                    break
                except (ValueError, TypeError):
                    pass
        
        # Add account to the list if we have both name and value
        if account_name and account_value is not None:
            account = {
                "name": account_name,
                "value": account_value
            }
            if account_code:
                account["code"] = account_code
            accounts.append(account)
    
    return accounts, total_value


def analyze_profit_loss(file_path):
    """
    Analyze a profit and loss Excel report and extract structured data.
    
    Args:
        file_path (str): Path to the Excel file.
        
    Returns:
        dict: Structured profit and loss data.
    """
    # Read the Excel file
    df = pd.read_excel(file_path)
    
    # Extract company name and period
    company_name, period = extract_company_and_period(df)
    
    # Identify basis type (Accrual or Cash)
    basis_type = identify_basis_type(df)
    
    # Find section boundaries
    sections = find_section_boundaries(df)
    
    # Create result structure
    result = {
        "companyName": company_name if company_name else "Unknown Company",
        "period": period if period else "Unknown Period",
        "basisType": basis_type,
        "reportType": "Complete",
        "sections": {},
        "metadata": {
            "uploadDate": datetime.now().strftime("%Y-%m-%d"),
            "source": os.path.basename(file_path),
            "currency": "USD"  # Default, could be extracted from the file
        }
    }
    
    # Extract trading income
    if sections['tradingIncome']['start'] is not None and sections['tradingIncome']['end'] is not None:
        accounts, total = extract_accounts(df, sections['tradingIncome']['start'], sections['tradingIncome']['end'])
        if accounts:
            # Ensure we have a valid total (not zero or None)
            if total is None or abs(total) < 0.01:
                # Calculate the total from accounts
                total = sum(account["value"] for account in accounts)
                
            result["sections"]["tradingIncome"] = {
                "accounts": accounts,
                "total": total
            }
    
    # Extract cost of sales
    if sections['costOfSales']['start'] is not None and sections['costOfSales']['end'] is not None:
        accounts, total = extract_accounts(df, sections['costOfSales']['start'], sections['costOfSales']['end'])
        if accounts:
            # Ensure we have a valid total (not zero or None)
            if total is None or abs(total) < 0.01:
                # Calculate the total from accounts
                total = sum(account["value"] for account in accounts)
                
            result["sections"]["costOfSales"] = {
                "accounts": accounts,
                "total": total
            }
    
    # Extract gross profit
    if sections['grossProfit']['row'] is not None:
        row = df.iloc[sections['grossProfit']['row']]
        gross_profit_extracted = None
        
        # Try to extract gross profit from the row
        for i in range(len(row) - 1, -1, -1):
            if pd.notna(row.iloc[i]) and (isinstance(row.iloc[i], (int, float)) or 
                                         (isinstance(row.iloc[i], str) and row.iloc[i].replace('.', '', 1).replace('-', '', 1).isdigit())):
                try:
                    gross_profit_extracted = float(row.iloc[i])
                    break
                except (ValueError, TypeError):
                    pass
        
        # Calculate gross profit from income and cost of sales
        gross_profit_calculated = None
        if 'tradingIncome' in result['sections'] and 'costOfSales' in result['sections']:
            income_total = result['sections']['tradingIncome']['total']
            cost_total = result['sections']['costOfSales']['total']
            if income_total is not None and cost_total is not None:
                gross_profit_calculated = income_total - cost_total
        
        # Use calculated value if extracted is zero or None
        if gross_profit_extracted is None or abs(gross_profit_extracted) < 0.01:
            result["sections"]["grossProfit"] = gross_profit_calculated
        else:
            result["sections"]["grossProfit"] = gross_profit_extracted
    
    # Extract operating expenses
    if sections['operatingExpenses']['start'] is not None and sections['operatingExpenses']['end'] is not None:
        accounts, total = extract_accounts(df, sections['operatingExpenses']['start'], sections['operatingExpenses']['end'])
        if accounts:
            # Ensure we have a valid total (not zero or None)
            if total is None or abs(total) < 0.01:
                # Calculate the total from accounts
                total = sum(account["value"] for account in accounts)
                
            result["sections"]["operatingExpenses"] = {
                "accounts": accounts,
                "total": total
            }
    
    # Extract net profit
    if sections['netProfit']['row'] is not None:
        row = df.iloc[sections['netProfit']['row']]
        net_profit_extracted = None
        
        # Try to extract net profit from the row
        for i in range(len(row) - 1, -1, -1):
            if pd.notna(row.iloc[i]) and isinstance(row.iloc[i], (int, float)) or (isinstance(row.iloc[i], str) and row.iloc[i].replace('.', '', 1).replace('-', '', 1).isdigit()):
                try:
                    net_profit_extracted = float(row.iloc[i])
                    break
                except (ValueError, TypeError):
                    pass
        
        # Calculate net profit from gross profit and operating expenses
        net_profit_calculated = None
        if 'grossProfit' in result['sections'] and 'operatingExpenses' in result['sections']:
            gross_profit = result['sections']['grossProfit']
            operating_expenses_total = result['sections']['operatingExpenses']['total']
            if gross_profit is not None and operating_expenses_total is not None:
                net_profit_calculated = gross_profit - operating_expenses_total
        
        # Use calculated value if extracted is zero or None
        if net_profit_extracted is None or abs(net_profit_extracted) < 0.01:
            result["sections"]["netProfit"] = net_profit_calculated
        else:
            result["sections"]["netProfit"] = net_profit_extracted
    
    return result