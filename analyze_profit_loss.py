import pandas as pd
import json
import os
import re
from datetime import datetime

def extract_company_and_period(df):
    """Extract company name and period from the Excel file."""
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
    """Identify if the report is on Accrual or Cash basis."""
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
    """Find the row indices for each section of the profit and loss report."""
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
        'grossProfit': ['gross profit', 'gross income'],
        'operatingExpenses': ['operating expenses', 'expenses', 'overhead', 'operating costs', 'indirect costs'],
        'netProfit': ['net profit', 'net income', 'profit for the period', 'net earnings']
    }
    
    # Track the current section we're in to avoid overlapping
    current_section = None
    
    for i in range(len(df)):
        row = df.iloc[i]
        row_str = ' '.join(str(x) for x in row if pd.notna(x)).lower()
        
        # Check for section headers
        for section, keywords in section_keywords.items():
            if any(keyword in row_str for keyword in keywords):
                # If this is a new section, mark the end of the previous section
                if current_section and current_section != section and sections[current_section]['end'] is None:
                    sections[current_section]['end'] = i - 1
                
                if section in ['grossProfit', 'netProfit']:
                    sections[section]['row'] = i
                else:
                    if sections[section]['start'] is None:
                        sections[section]['start'] = i
                        current_section = section
                    
                    # If we find a total line for this section, mark it as the end
                    if 'total' in row_str and any(keyword in row_str for keyword in keywords):
                        sections[section]['end'] = i
                        current_section = None
    
    # Infer section boundaries if not explicitly found
    for section in ['tradingIncome', 'costOfSales', 'operatingExpenses']:
        if sections[section]['start'] is not None and sections[section]['end'] is None:
            # Look for the next section or a total line
            for i in range(sections[section]['start'] + 1, len(df)):
                row_str = ' '.join(str(x) for x in df.iloc[i] if pd.notna(x)).lower()
                if 'total' in row_str:
                    sections[section]['end'] = i
                    break
                
                # Check if we've hit the next section
                for next_section, keywords in section_keywords.items():
                    if next_section != section and any(keyword in row_str for keyword in keywords):
                        sections[section]['end'] = i - 1
                        break
                        
                if sections[section]['end'] is not None:
                    break
    
    return sections

def extract_accounts(df, start_idx, end_idx):
    """Extract account details from a section of the profit and loss report."""
    accounts = []
    extracted_total = None
    calculated_total = None
    
    # Find the column with numeric values (usually the last non-empty column)
    value_col = None
    for i in range(len(df.columns) - 1, -1, -1):
        if pd.notna(df.iloc[start_idx:end_idx+1, i]).any():
            value_col = i
            break
    
    if value_col is None:
        return accounts, None
    
    # Extract accounts and values
    for i in range(start_idx + 1, end_idx + 1):
        row = df.iloc[i]
        
        # Skip empty rows
        if pd.isna(row).all() or all(str(x).strip() == '' for x in row if pd.notna(x)):
            continue
        
        # Check if this is a total row
        row_str = ' '.join(str(x) for x in row if pd.notna(x)).lower()
        if 'total' in row_str:
            try:
                extracted_total = float(row.iloc[value_col])
            except (ValueError, TypeError):
                pass
            continue
        
        # Skip rows that indicate the start of another section
        if any(keyword in row_str.lower() for keyword in ['cost of sales', 'cost of goods sold', 'cogs', 'direct costs', 'gross profit', 'operating expenses']):
            continue
        
        # Extract account code if available (usually in the first column)
        code = None
        name = None
        value = None
        
        # Look for account code (usually numeric or alphanumeric code in first columns)
        for j in range(min(2, len(row))):
            if pd.notna(row.iloc[j]) and re.match(r'^[A-Z0-9-]+$', str(row.iloc[j]).strip()):
                code = str(row.iloc[j]).strip()
                break
        
        # Extract account name (usually in the leftmost non-empty cell if not the code)
        for j in range(len(row)):
            if pd.notna(row.iloc[j]) and (code is None or str(row.iloc[j]) != code):
                name = str(row.iloc[j]).strip()
                break
        
        # Extract value (usually in the rightmost non-empty cell)
        try:
            value = float(row.iloc[value_col])
        except (ValueError, TypeError):
            continue
        
        if name and value is not None:
            account = {"name": name}
            if code:
                account["code"] = code
            account["value"] = value
            accounts.append(account)
    
    # Calculate total from account values
    if accounts:
        calculated_total = sum(account["value"] for account in accounts)
    
    # Determine which total to use
    # If extracted_total is None or zero, use calculated_total
    # Otherwise, if extracted and calculated totals differ significantly, use calculated_total
    if extracted_total is None or abs(extracted_total) < 0.01:  # Consider zero if less than 0.01
        return accounts, calculated_total
    elif calculated_total is not None and abs(extracted_total - calculated_total) > max(abs(extracted_total), abs(calculated_total)) * 0.05:  # 5% difference threshold
        # If difference is more than 5%, use calculated total
        return accounts, calculated_total
    else:
        return accounts, extracted_total
    
    return accounts, total

def analyze_profit_loss(file_path):
    """Analyze a profit and loss Excel file and extract structured data."""
    # Read the Excel file
    df = pd.read_excel(file_path, header=None)
    
    # Extract company name and period
    company_name, period = extract_company_and_period(df)
    
    # Identify basis type
    basis_type = identify_basis_type(df)
    
    # Find section boundaries
    sections = find_section_boundaries(df)
    
    # Determine if the report is complete or partial
    report_type = "Complete"
    if sections['tradingIncome']['start'] is None or sections['costOfSales']['start'] is None:
        report_type = "Partial"
    
    # Initialize result structure
    result = {
        "companyName": company_name,
        "period": period,
        "basisType": basis_type,
        "reportType": report_type,
        "sections": {}
    }
    
    # Extract trading income - ensure we don't include Cost of Sales rows
    if sections['tradingIncome']['start'] is not None and sections['tradingIncome']['end'] is not None:
        # If Cost of Sales starts before Trading Income ends, adjust the end boundary
        if (sections['costOfSales']['start'] is not None and 
            sections['tradingIncome']['start'] < sections['costOfSales']['start'] < sections['tradingIncome']['end']):
            trading_end = sections['costOfSales']['start'] - 1
        else:
            trading_end = sections['tradingIncome']['end']
            
        accounts, total = extract_accounts(df, sections['tradingIncome']['start'], trading_end)
        
        # Get the total trading income from the Trading Income section
        trading_total = None
        for i in range(sections['tradingIncome']['start'], trading_end + 1):
            row = df.iloc[i]
            row_str = ' '.join(str(x) for x in row if pd.notna(x)).lower()
            if 'total' in row_str and any(keyword in row_str for keyword in ['trading income', 'revenue', 'sales', 'income']):
                # Find the value column
                for j in range(len(df.columns) - 1, -1, -1):
                    if pd.notna(row.iloc[j]) and isinstance(row.iloc[j], (int, float)) or (isinstance(row.iloc[j], str) and row.iloc[j].replace('.', '', 1).replace('-', '', 1).isdigit()):
                        try:
                            trading_total = float(row.iloc[j])
                            break
                        except (ValueError, TypeError):
                            pass
        
        if accounts:
            # If trading_total is None or zero, use the calculated total
            if trading_total is None or abs(trading_total) < 0.01:
                trading_total = total
            
            result["sections"]["tradingIncome"] = {
                "accounts": accounts,
                "total": trading_total
            }
    
    # Extract cost of sales
    if sections['costOfSales']['start'] is not None and sections['costOfSales']['end'] is not None:
        accounts, total = extract_accounts(df, sections['costOfSales']['start'], sections['costOfSales']['end'])
        if accounts:
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
            if pd.notna(row.iloc[i]) and isinstance(row.iloc[i], (int, float)) or (isinstance(row.iloc[i], str) and row.iloc[i].replace('.', '', 1).isdigit()):
                try:
                    gross_profit_extracted = float(row.iloc[i])
                    break
                except (ValueError, TypeError):
                    pass
        
        # Calculate gross profit from trading income and cost of sales
        gross_profit_calculated = None
        if 'tradingIncome' in result['sections'] and 'costOfSales' in result['sections']:
            trading_income_total = result['sections']['tradingIncome']['total']
            cost_of_sales_total = result['sections']['costOfSales']['total']
            if trading_income_total is not None and cost_of_sales_total is not None:
                gross_profit_calculated = trading_income_total - cost_of_sales_total
        
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

