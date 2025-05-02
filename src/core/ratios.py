"""
Financial ratios and metrics calculation module.

This module provides functions and Pydantic models for calculating key financial ratios
and metrics for profit and loss analysis.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

# Import centralized logger
from src.utils.logger import app_logger as logger

class FinancialStatement(BaseModel):
    revenue: float = Field(..., description="Total revenue (sales)")
    cost_of_goods_sold: Optional[float] = Field(None, description="Cost of goods sold (COGS)")
    operating_expenses: Optional[float] = Field(None, description="Operating expenses")
    net_income: Optional[float] = Field(None, description="Net income (profit after tax)")
    total_assets: Optional[float] = Field(None, description="Total assets")
    total_equity: Optional[float] = Field(None, description="Total equity")
    current_assets: Optional[float] = Field(None, description="Current assets")
    current_liabilities: Optional[float] = Field(None, description="Current liabilities")
    cash: Optional[float] = Field(None, description="Cash and cash equivalents")
    inventory: Optional[float] = Field(None, description="Inventory")
    accounts_receivable: Optional[float] = Field(None, description="Accounts receivable")

    @field_validator('*', mode='before')
    @classmethod
    def none_to_zero(cls, v):
        return v if v is not None else 0.0


def gross_margin_ratio(fs: FinancialStatement) -> Optional[float]:
    """
    Calculate the gross margin ratio.
    Args:
        fs (FinancialStatement): Financial statement data.
    Returns:
        Optional[float]: Gross margin ratio, or None if not computable.
    """
    try:
        if fs.revenue == 0:
            logger.warning("Revenue is zero, cannot compute gross margin ratio.")
            return None
        gross_profit = fs.revenue - fs.cost_of_goods_sold
        return gross_profit / fs.revenue
    except Exception as e:
        logger.error(f"Error calculating gross margin ratio: {e}")
        return None

def net_margin_ratio(fs: FinancialStatement) -> Optional[float]:
    """
    Calculate the net margin ratio.
    Args:
        fs (FinancialStatement): Financial statement data.
    Returns:
        Optional[float]: Net margin ratio, or None if not computable.
    """
    try:
        if fs.revenue == 0:
            logger.warning("Revenue is zero, cannot compute net margin ratio.")
            return None
        return fs.net_income / fs.revenue
    except Exception as e:
        logger.error(f"Error calculating net margin ratio: {e}")
        return None

def operating_margin_ratio(fs: FinancialStatement) -> Optional[float]:
    """
    Calculate the operating margin ratio.
    Args:
        fs (FinancialStatement): Financial statement data.
    Returns:
        Optional[float]: Operating margin ratio, or None if not computable.
    """
    try:
        if fs.revenue == 0:
            logger.warning("Revenue is zero, cannot compute operating margin ratio.")
            return None
        op_profit = fs.revenue - fs.cost_of_goods_sold - fs.operating_expenses
        return op_profit / fs.revenue
    except Exception as e:
        logger.error(f"Error calculating operating margin ratio: {e}")
        return None

def return_on_equity(fs: FinancialStatement) -> Optional[float]:
    """
    Calculate return on equity (ROE).
    Args:
        fs (FinancialStatement): Financial statement data.
    Returns:
        Optional[float]: ROE, or None if not computable.
    """
    try:
        if fs.total_equity == 0:
            logger.warning("Total equity is zero, cannot compute ROE.")
            return None
        return fs.net_income / fs.total_equity
    except Exception as e:
        logger.error(f"Error calculating ROE: {e}")
        return None

def return_on_assets(fs: FinancialStatement) -> Optional[float]:
    """
    Calculate return on assets (ROA).
    Args:
        fs (FinancialStatement): Financial statement data.
    Returns:
        Optional[float]: ROA, or None if not computable.
    """
    try:
        if fs.total_assets == 0:
            logger.warning("Total assets is zero, cannot compute ROA.")
            return None
        return fs.net_income / fs.total_assets
    except Exception as e:
        logger.error(f"Error calculating ROA: {e}")
        return None

def current_ratio(fs: FinancialStatement) -> Optional[float]:
    """
    Calculate the current ratio.
    Args:
        fs (FinancialStatement): Financial statement data.
    Returns:
        Optional[float]: Current ratio, or None if not computable.
    """
    try:
        if fs.current_liabilities == 0:
            logger.warning("Current liabilities is zero, cannot compute current ratio.")
            return None
        return fs.current_assets / fs.current_liabilities
    except Exception as e:
        logger.error(f"Error calculating current ratio: {e}")
        return None

def quick_ratio(fs: FinancialStatement) -> Optional[float]:
    """
    Calculate the quick ratio (acid-test ratio).
    
    Args:
        fs (FinancialStatement): Financial statement data.
        
    Returns:
        Optional[float]: Quick ratio, or None if not computable.
    """
    try:
        if fs.current_liabilities == 0:
            logger.warning("Current liabilities is zero, cannot compute quick ratio.")
            return None
        quick_assets = fs.current_assets - fs.inventory
        return quick_assets / fs.current_liabilities
    except Exception as e:
        logger.error(f"Error calculating quick ratio: {e}")
        return None


def convert_analyzer_output_to_financial_statement(data: Dict[str, Any]) -> FinancialStatement:
    """
    Convert analyzer output to FinancialStatement model.
    
    Args:
        data (Dict[str, Any]): The profit and loss data dictionary from analyzer.
        
    Returns:
        FinancialStatement: A FinancialStatement object with data from analyzer output.
        
    Raises:
        ValueError: If required fields are missing from the analyzer output.
    """
    sections = data.get('sections', {})
    
    # Extract required fields
    if 'tradingIncome' not in sections:
        raise ValueError("Missing required field 'tradingIncome' in analyzer output")
    
    # Extract values with defaults
    revenue = sections.get('tradingIncome', {}).get('total', 0)
    cost_of_goods_sold = sections.get('costOfSales', {}).get('total', 0)
    operating_expenses = sections.get('operatingExpenses', {}).get('total', 0)
    net_income = sections.get('netProfit', 0)
    
    # Create FinancialStatement object
    return FinancialStatement(
        revenue=revenue,
        cost_of_goods_sold=cost_of_goods_sold,
        operating_expenses=operating_expenses,
        net_income=net_income,
        # Balance sheet items are not available in P&L data
        # but we include them with None values for completeness
        total_assets=None,
        total_equity=None,
        current_assets=None,
        current_liabilities=None,
        cash=None,
        inventory=None,
        accounts_receivable=None
    )


def calculate_all_ratios(fs: FinancialStatement) -> Dict[str, Optional[float]]:
    """
    Calculate all available financial ratios.
    
    Args:
        fs (FinancialStatement): Financial statement data.
        
    Returns:
        Dict[str, Optional[float]]: Dictionary of all calculated ratios.
    """
    ratios = {
        'gross_margin': gross_margin_ratio(fs),
        'net_margin': net_margin_ratio(fs),
        'operating_margin': operating_margin_ratio(fs),
        'return_on_equity': return_on_equity(fs),
        'return_on_assets': return_on_assets(fs),
        'current_ratio': current_ratio(fs),
        'quick_ratio': quick_ratio(fs)
    }
    
    # Convert to percentages for margin ratios
    for key in ['gross_margin', 'net_margin', 'operating_margin', 'return_on_equity', 'return_on_assets']:
        if ratios[key] is not None:
            ratios[key] = ratios[key] * 100
    
    return ratios


def calculate_financial_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate financial metrics from analyzer output.
    
    This is the main function to be used by the dashboard to get all financial metrics.
    
    Args:
        data (Dict[str, Any]): The profit and loss data dictionary from analyzer.
        
    Returns:
        Dict[str, Any]: Dictionary containing all financial metrics and ratios.
    """
    try:
        # Convert analyzer output to FinancialStatement
        fs = convert_analyzer_output_to_financial_statement(data)
        
        # Calculate all ratios
        ratios = calculate_all_ratios(fs)
        
        # Add additional metrics
        metrics = {
            'gross_profit': fs.revenue - fs.cost_of_goods_sold,
            'operating_profit': fs.revenue - fs.cost_of_goods_sold - fs.operating_expenses,
            'cogs_ratio': (fs.cost_of_goods_sold / fs.revenue * 100) if fs.revenue != 0 else None,
            'expense_ratio': (fs.operating_expenses / fs.revenue * 100) if fs.revenue != 0 else None
        }
        
        # Combine ratios and metrics
        return {**ratios, **metrics}
    except Exception as e:
        logger.error(f"Error calculating financial metrics: {e}")
        return {}
