"""
Category-based visualization components for the Profitability Analysis Dashboard.

This module provides functions to create visualizations for account categories,
helping to analyze financial data by business categories.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional


def create_category_pie_chart(category_totals: Dict[str, float], title: str = "Distribution by Category") -> go.Figure:
    """
    Create a pie chart showing the distribution of values by category.
    
    Args:
        category_totals: Dictionary with categories as keys and total values as values.
        title: Chart title.
        
    Returns:
        Plotly figure object.
    """
    # Create DataFrame for the chart
    df = pd.DataFrame({
        'Category': list(category_totals.keys()),
        'Value': list(category_totals.values())
    })
    
    # Use absolute values for the pie chart
    df['AbsValue'] = df['Value'].abs()
    
    # Create pie chart
    fig = px.pie(
        df, 
        names='Category', 
        values='AbsValue',
        title=title,
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Improve layout
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=50, b=100)
    )
    
    # Add percentage labels
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        insidetextfont=dict(color='white')
    )
    
    return fig


def create_category_bar_chart(category_totals: Dict[str, float], title: str = "Category Analysis") -> go.Figure:
    """
    Create a horizontal bar chart showing categories by value.
    
    Args:
        category_totals: Dictionary with categories as keys and total values as values.
        title: Chart title.
        
    Returns:
        Plotly figure object.
    """
    # Create DataFrame for the chart
    df = pd.DataFrame({
        'Category': list(category_totals.keys()),
        'Value': list(category_totals.values())
    })
    
    # Sort by absolute value
    df['AbsValue'] = df['Value'].abs()
    df = df.sort_values('AbsValue', ascending=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        df,
        x='Value',
        y='Category',
        orientation='h',
        title=title,
        color='Category',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title="Amount",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Add value labels
    fig.update_traces(
        texttemplate='%{x:$.2f}',
        textposition='outside'
    )
    
    return fig


def create_category_treemap(category_totals: Dict[str, float], title: str = "Category Breakdown") -> go.Figure:
    """
    Create a treemap visualization of categories.
    
    Args:
        category_totals: Dictionary with categories as keys and total values as values.
        title: Chart title.
        
    Returns:
        Plotly figure object.
    """
    # Create DataFrame for the chart
    df = pd.DataFrame({
        'Category': list(category_totals.keys()),
        'Value': list(category_totals.values())
    })
    
    # Use absolute values for the treemap
    df['AbsValue'] = df['Value'].abs()
    
    # Create treemap
    fig = px.treemap(
        df,
        path=['Category'],
        values='AbsValue',
        title=title,
        color='Category',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Improve layout
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Add value labels
    fig.update_traces(
        texttemplate='%{label}<br>%{value:$.2f}',
        textposition='middle center'
    )
    
    return fig


def create_category_comparison_chart(data: Dict[str, Any]) -> go.Figure:
    """
    Create a comparison chart showing categories across different sections.
    
    Args:
        data: The profit and loss data dictionary with categorized accounts.
        
    Returns:
        Plotly figure object.
    """
    # Extract sections
    sections = data.get('sections', {})
    categories = {}
    
    # Process each section with accounts
    for section_name, section_data in sections.items():
        if isinstance(section_data, dict) and 'accounts' in section_data:
            for account in section_data['accounts']:
                category = account.get('category', 'Uncategorized')
                section_display = section_name
                
                # Make section names more readable
                if section_name == 'tradingIncome':
                    section_display = 'Income'
                elif section_name == 'costOfSales':
                    section_display = 'Cost of Sales'
                elif section_name == 'operatingExpenses':
                    section_display = 'Expenses'
                
                if category not in categories:
                    categories[category] = {}
                
                if section_display not in categories[category]:
                    categories[category][section_display] = 0
                
                categories[category][section_display] += account.get('value', 0)
    
    # Prepare data for the chart
    chart_data = []
    for category, section_values in categories.items():
        for section, value in section_values.items():
            chart_data.append({
                'Category': category,
                'Section': section,
                'Value': value,
                'AbsValue': abs(value)
            })
    
    # Create DataFrame
    df = pd.DataFrame(chart_data)
    
    # Create grouped bar chart
    fig = px.bar(
        df,
        x='Category',
        y='Value',
        color='Section',
        title='Category Comparison Across Sections',
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Amount",
        legend_title="Section",
        margin=dict(l=20, r=20, t=50, b=100)
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)
    
    return fig
