"""
Visualization components for the Profitability Analysis Dashboard.

This module contains functions for creating various charts and visualizations
used in the Streamlit dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional, Union


def create_profit_breakdown_chart(data: Dict[str, Any]) -> go.Figure:
    """
    Create a waterfall chart showing the profit breakdown.
    
    Args:
        data: The profit and loss data dictionary.
        
    Returns:
        Plotly figure object with the waterfall chart.
    """
    sections = data.get('sections', {})
    
    # Get values (with defaults of 0 if not present)
    trading_income = sections.get('tradingIncome', {}).get('total', 0)
    cost_of_sales = abs(sections.get('costOfSales', {}).get('total', 0))
    operating_expenses = abs(sections.get('operatingExpenses', {}).get('total', 0))
    net_profit = sections.get('netProfit', 0)
    
    fig = go.Figure()
    
    # Create a waterfall chart
    fig.add_trace(go.Waterfall(
        name="Financial Flow",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Trading Income", "Cost of Sales", "Operating Expenses", "Net Profit"],
        textposition="outside",
        text=[f"${trading_income:,.2f}", f"${cost_of_sales:,.2f}", f"${operating_expenses:,.2f}", f"${net_profit:,.2f}"],
        y=[trading_income, -cost_of_sales, -operating_expenses, net_profit],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title="Profit Breakdown",
        showlegend=False,
        height=400
    )
    
    return fig


def create_expense_breakdown_chart(
    expense_accounts: List[Dict[str, Any]],
    chart_type: str = "Pie Chart"
) -> go.Figure:
    """
    Create a chart showing the breakdown of expenses.
    
    Args:
        expense_accounts: List of expense account dictionaries.
        chart_type: Type of chart to create (Pie Chart, Treemap, or Bar Chart).
        
    Returns:
        Plotly figure object with the expense breakdown chart.
    """
    # Convert to DataFrame
    expense_df = pd.DataFrame(expense_accounts)
    
    if expense_df.empty:
        # Return an empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Expense Breakdown (No Data)",
            height=400
        )
        return fig
    
    # Ensure value column is numeric and take absolute value
    expense_df['value'] = expense_df['value'].abs()
    
    # Create chart based on type
    if chart_type == "Pie Chart":
        fig = px.pie(
            expense_df,
            values='value',
            names='name',
            title="Expense Breakdown",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
    elif chart_type == "Treemap":
        fig = px.treemap(
            expense_df,
            values='value',
            names='name',
            title="Expense Breakdown",
            color='value',
            color_continuous_scale='Blues',
        )
        fig.update_traces(textinfo='label+value+percent parent')
        
    else:  # Bar Chart
        # Sort by value descending
        expense_df = expense_df.sort_values('value', ascending=False)
        
        fig = px.bar(
            expense_df,
            y='name',
            x='value',
            title="Expense Breakdown",
            orientation='h',
            color='value',
            color_continuous_scale='Blues',
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    
    fig.update_layout(height=400)
    return fig


def create_income_breakdown_chart(income_accounts: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a chart showing the breakdown of income.
    
    Args:
        income_accounts: List of income account dictionaries.
        
    Returns:
        Plotly figure object with the income breakdown chart.
    """
    # Convert to DataFrame
    income_df = pd.DataFrame(income_accounts)
    
    if income_df.empty:
        # Return an empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Income Breakdown (No Data)",
            height=400
        )
        return fig
    
    # Create pie chart
    fig = px.pie(
        income_df,
        values='value',
        names='name',
        title="Income Breakdown",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Greens_r
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    fig.update_layout(height=400)
    return fig


def create_financial_metrics_gauge(ratios: Dict[str, float]) -> go.Figure:
    """
    Create gauge charts for financial metrics.
    
    Args:
        ratios: Dictionary of financial ratios.
        
    Returns:
        Plotly figure object with gauge charts.
    """
    # Create a subplot with 2x2 grid
    fig = go.Figure()
    
    # Gross Margin Gauge
    fig.add_trace(create_gauge_chart(
        title="Gross Margin",
        metric_value=ratios['gross_margin'],
        suffix="%",
        threshold_poor=20,
        threshold_good=40,
        max_value=60
    ))
    
    # Net Margin Gauge
    fig.add_trace(create_gauge_chart(
        title="Net Margin",
        metric_value=ratios['net_margin'],
        suffix="%",
        threshold_poor=5,
        threshold_good=15,
        max_value=30
    ))
    
    # Expense Ratio Gauge
    fig.add_trace(create_gauge_chart(
        title="Expense Ratio",
        metric_value=ratios['expense_ratio'],
        suffix="%",
        threshold_poor=40,
        threshold_good=20,
        max_value=60,
        is_inverted=True
    ))
    
    # COGS Ratio Gauge
    fig.add_trace(create_gauge_chart(
        title="COGS Ratio",
        metric_value=ratios['cogs_ratio'],
        suffix="%",
        threshold_poor=70,
        threshold_good=50,
        max_value=100,
        is_inverted=True
    ))
    
    # Update layout for 2x2 grid
    fig.update_layout(
        grid=dict(rows=2, columns=2),
        height=500,
        title="Financial Metrics"
    )
    
    return fig


def create_gauge_chart(
    title: str,
    metric_value: float,
    suffix: str = "%",
    threshold_poor: float = 20,
    threshold_good: float = 40,
    max_value: float = 100,
    is_inverted: bool = False
) -> go.Indicator:
    """
    Create a gauge chart for a single metric.
    
    Args:
        title: Title of the gauge.
        metric_value: Value to display.
        suffix: Suffix for the value (e.g., "%").
        threshold_poor: Threshold for poor performance.
        threshold_good: Threshold for good performance.
        max_value: Maximum value for the gauge.
        is_inverted: Whether higher values are worse (inverted color scheme).
        
    Returns:
        Plotly indicator trace.
    """
    # For inverted metrics (where lower is better), swap colors
    if is_inverted:
        color_poor = "red"
        color_good = "green"
    else:
        color_poor = "green"
        color_good = "red"
    
    return go.Indicator(
        mode="gauge+number",
        value=metric_value,
        title={"text": title},
        number={"suffix": suffix},
        gauge={
            "axis": {"range": [None, max_value]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, threshold_poor], "color": color_poor},
                {"range": [threshold_poor, threshold_good], "color": "gray"},
                {"range": [threshold_good, max_value], "color": "lightgray"}
            ],
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": metric_value
            }
        }
    )


def create_financial_summary_table(data: Dict[str, Any]) -> go.Figure:
    """
    Create a table visualization of financial summary data.
    
    Args:
        data: Dictionary containing financial summary data.
        
    Returns:
        Plotly figure object with the table.
    """
    sections = data.get('sections', {})
    
    # Prepare data for table
    table_data = []
    
    # Trading Income
    if 'tradingIncome' in sections:
        table_data.append(["Trading Income", f"${sections['tradingIncome'].get('total', 0):,.2f}"])
    
    # Cost of Sales
    if 'costOfSales' in sections:
        table_data.append(["Cost of Sales", f"${sections['costOfSales'].get('total', 0):,.2f}"])
    
    # Gross Profit
    if 'grossProfit' in sections:
        table_data.append(["Gross Profit", f"${sections['grossProfit']:,.2f}"])
    
    # Operating Expenses
    if 'operatingExpenses' in sections:
        table_data.append(["Operating Expenses", f"${sections['operatingExpenses'].get('total', 0):,.2f}"])
    
    # Net Profit
    if 'netProfit' in sections:
        table_data.append(["Net Profit", f"${sections['netProfit']:,.2f}"])
    
    # Create table
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["Item", "Amount"],
            fill_color='#1E88E5',
            align='left',
            font=dict(color='white', size=14)
        ),
        cells=dict(
            values=list(zip(*table_data)),
            fill_color='lavender',
            align='left'
        )
    )])
    
    fig.update_layout(
        title="Financial Summary",
        height=300
    )
    
    return fig