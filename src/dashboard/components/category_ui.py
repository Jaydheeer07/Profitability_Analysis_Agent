"""
Category analysis UI components for the Profitability Analysis Dashboard.

This module provides UI components for displaying category-based analysis
of financial accounts in the Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
import traceback
from typing import Dict, List, Any, Optional

from src.dashboard.utils import format_currency
from src.utils.categorization import get_accounts_by_category, get_category_totals
from src.dashboard.visualizations.category_charts import (
    create_category_pie_chart,
    create_category_bar_chart,
    create_category_treemap,
    create_category_comparison_chart
)
from src.utils.logger import app_logger

# Configure module-specific logger
logger = app_logger.getChild('category_ui')


def render_category_analysis(data: Dict[str, Any]) -> None:
    """
    Render category-based analysis of accounts.
    
    Args:
        data: The profit and loss data dictionary.
    """
    logger.info("Rendering category analysis UI")
    st.markdown("<div class='section-header'>Category Analysis</div>", unsafe_allow_html=True)
    
    try:
        # Create tabs for different category views
        tabs = st.tabs([
            "Overview", 
            "Income Categories", 
            "Cost Categories", 
            "Expense Categories",
            "Category Comparison"
        ])
        
        logger.debug("Created category analysis tabs")
    except Exception as e:
        logger.error(f"Error creating category tabs: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("Error setting up category analysis. Please check the logs for details.")
        return
    
    # Overview tab
    with tabs[0]:
        try:
            logger.debug("Rendering Overview tab")
            # All categories across sections
            category_totals = get_category_totals(data)
            logger.debug(f"Retrieved {len(category_totals)} category totals")
            
            if category_totals:
                # Create columns for table and chart
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Create DataFrame for display
                    df = pd.DataFrame({
                        'Category': list(category_totals.keys()),
                        'Total': list(category_totals.values())
                    })
                    
                    # Sort by absolute value
                    df['AbsTotal'] = df['Total'].abs()
                    df = df.sort_values('AbsTotal', ascending=False).drop('AbsTotal', axis=1)
                    
                    # Format totals
                    df['Total'] = df['Total'].apply(format_currency)
                    
                    # Display as table
                    st.dataframe(df, use_container_width=True)
                
                with col2:
                    # Visualization options
                    chart_type = st.radio(
                        "Select visualization type:",
                        ["Pie Chart", "Treemap", "Bar Chart"],
                        horizontal=True
                    )
                    
                    try:
                        # Create selected chart
                        logger.debug(f"Creating {chart_type} for category totals")
                        if chart_type == "Pie Chart":
                            fig = create_category_pie_chart(category_totals, "Overall Category Distribution")
                        elif chart_type == "Treemap":
                            fig = create_category_treemap(category_totals, "Overall Category Breakdown")
                        else:  # Bar Chart
                            fig = create_category_bar_chart(category_totals, "Overall Category Analysis")
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        logger.error(f"Error creating {chart_type}: {str(e)}")
                        logger.error(traceback.format_exc())
                        st.error(f"Error creating {chart_type}. Please try a different visualization type.")
            else:
                st.info("No category data available.")
        except Exception as e:
            logger.error(f"Error rendering overview tab: {str(e)}")
            logger.error(traceback.format_exc())
            st.error("Error rendering category overview. Please check the logs for details.")
    
    # Income Categories tab
    with tabs[1]:
        try:
            logger.debug("Rendering Income Categories tab")
            # Income categories
            income_categories = get_category_totals(data, 'tradingIncome')
            logger.debug(f"Retrieved {len(income_categories)} income categories")
            
            if income_categories:
                # Create columns for table and chart
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Create DataFrame for display
                    df = pd.DataFrame({
                        'Category': list(income_categories.keys()),
                        'Total': list(income_categories.values())
                    })
                    
                    # Sort by absolute value
                    df['AbsTotal'] = df['Total'].abs()
                    df = df.sort_values('AbsTotal', ascending=False).drop('AbsTotal', axis=1)
                    
                    # Format totals
                    df['Total'] = df['Total'].apply(format_currency)
                    
                    # Display as table
                    st.dataframe(df, use_container_width=True)
                
                with col2:
                    # Create pie chart for income categories
                    fig = create_category_pie_chart(income_categories, "Income Category Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show detailed accounts by category
                    with st.expander("View Income Accounts by Category"):
                        try:
                            income_by_category = get_accounts_by_category(data, 'tradingIncome')
                            
                            for category, accounts in income_by_category.items():
                                st.subheader(category)
                                
                                # Create DataFrame for display
                                df = pd.DataFrame(accounts)
                                
                                # Format value column
                                df['value'] = df['value'].apply(format_currency)
                                
                                # Rename columns for display
                                rename_dict = {
                                    'name': 'Account Name',
                                    'value': 'Amount'
                                }
                                
                                # Only include code if it exists
                                if 'code' in df.columns:
                                    rename_dict['code'] = 'Account Code'
                                
                                df = df.rename(columns=rename_dict)
                                
                                # Determine which columns to display
                                display_columns = ['Account Name']
                                if 'Account Code' in df.columns:
                                    display_columns.append('Account Code')
                                display_columns.append('Amount')
                                
                                # Display accounts in this category
                                st.dataframe(df[display_columns], use_container_width=True)
                        except Exception as e:
                            logger.error(f"Error displaying income accounts by category: {str(e)}")
                            logger.error(traceback.format_exc())
                            st.error("Error displaying income accounts by category. Please check the logs for details.")
            else:
                st.info("No income category data available.")
        except Exception as e:
            logger.error(f"Error rendering income categories tab: {str(e)}")
            logger.error(traceback.format_exc())
            st.error("Error rendering income categories. Please check the logs for details.")
    
    # Cost Categories tab
    with tabs[2]:
        try:
            logger.debug("Rendering Cost Categories tab")
            # Cost categories
            cost_categories = get_category_totals(data, 'costOfSales')
            logger.debug(f"Retrieved {len(cost_categories)} cost categories")
            
            if cost_categories:
                # Create columns for table and chart
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Create DataFrame for display
                    df = pd.DataFrame({
                        'Category': list(cost_categories.keys()),
                        'Total': list(cost_categories.values())
                    })
                    
                    # Sort by absolute value
                    df['AbsTotal'] = df['Total'].abs()
                    df = df.sort_values('AbsTotal', ascending=False).drop('AbsTotal', axis=1)
                    
                    # Format totals
                    df['Total'] = df['Total'].apply(format_currency)
                    
                    # Display as table
                    st.dataframe(df, use_container_width=True)
                
                with col2:
                    # Create pie chart for cost categories
                    fig = create_category_pie_chart(cost_categories, "Cost Category Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show detailed accounts by category
                    with st.expander("View Cost Accounts by Category"):
                        try:
                            costs_by_category = get_accounts_by_category(data, 'costOfSales')
                            
                            for category, accounts in costs_by_category.items():
                                st.subheader(category)
                                
                                # Create DataFrame for display
                                df = pd.DataFrame(accounts)
                                
                                # Format value column
                                df['value'] = df['value'].apply(format_currency)
                                
                                # Rename columns for display
                                rename_dict = {
                                    'name': 'Account Name',
                                    'value': 'Amount'
                                }
                                
                                # Only include code if it exists
                                if 'code' in df.columns:
                                    rename_dict['code'] = 'Account Code'
                                
                                df = df.rename(columns=rename_dict)
                                
                                # Determine which columns to display
                                display_columns = ['Account Name']
                                if 'Account Code' in df.columns:
                                    display_columns.append('Account Code')
                                display_columns.append('Amount')
                                
                                # Display accounts in this category
                                st.dataframe(df[display_columns], use_container_width=True)
                        except Exception as e:
                            logger.error(f"Error displaying cost accounts by category: {str(e)}")
                            logger.error(traceback.format_exc())
                            st.error("Error displaying cost accounts by category. Please check the logs for details.")
            else:
                st.info("No cost category data available.")
        except Exception as e:
            logger.error(f"Error rendering cost categories tab: {str(e)}")
            logger.error(traceback.format_exc())
            st.error("Error rendering cost categories. Please check the logs for details.")
    
    # Expense Categories tab
    with tabs[3]:
        try:
            logger.debug("Rendering Expense Categories tab")
            # Expense categories
            expense_categories = get_category_totals(data, 'operatingExpenses')
            logger.debug(f"Retrieved {len(expense_categories)} expense categories")
            
            if expense_categories:
                # Create columns for table and chart
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Create DataFrame for display
                    df = pd.DataFrame({
                        'Category': list(expense_categories.keys()),
                        'Total': list(expense_categories.values())
                    })
                    
                    # Sort by absolute value
                    df['AbsTotal'] = df['Total'].abs()
                    df = df.sort_values('AbsTotal', ascending=False).drop('AbsTotal', axis=1)
                    
                    # Format totals
                    df['Total'] = df['Total'].apply(format_currency)
                    
                    # Display as table
                    st.dataframe(df, use_container_width=True)
                
                with col2:
                    # Create pie chart for expense categories
                    fig = create_category_pie_chart(expense_categories, "Expense Category Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show detailed accounts by category
                    with st.expander("View Expense Accounts by Category"):
                        try:
                            expenses_by_category = get_accounts_by_category(data, 'operatingExpenses')
                            
                            for category, accounts in expenses_by_category.items():
                                st.subheader(category)
                                
                                # Create DataFrame for display
                                df = pd.DataFrame(accounts)
                                
                                # Format value column
                                df['value'] = df['value'].apply(format_currency)
                                
                                # Rename columns for display
                                rename_dict = {
                                    'name': 'Account Name',
                                    'value': 'Amount'
                                }
                                
                                # Only include code if it exists
                                if 'code' in df.columns:
                                    rename_dict['code'] = 'Account Code'
                                
                                df = df.rename(columns=rename_dict)
                                
                                # Determine which columns to display
                                display_columns = ['Account Name']
                                if 'Account Code' in df.columns:
                                    display_columns.append('Account Code')
                                display_columns.append('Amount')
                                
                                # Display accounts in this category
                                st.dataframe(df[display_columns], use_container_width=True)
                        except Exception as e:
                            logger.error(f"Error displaying expense accounts by category: {str(e)}")
                            logger.error(traceback.format_exc())
                            st.error("Error displaying expense accounts by category. Please check the logs for details.")
            else:
                st.info("No expense category data available.")
        except Exception as e:
            logger.error(f"Error rendering expense categories tab: {str(e)}")
            logger.error(traceback.format_exc())
            st.error("Error rendering expense categories. Please check the logs for details.")
    
    # Category Comparison tab
    with tabs[4]:
        try:
            logger.debug("Rendering Category Comparison tab")
            # Create comparison chart
            fig = create_category_comparison_chart(data)
            st.plotly_chart(fig, use_container_width=True)
            
            logger.debug("Category comparison chart rendered successfully")
            
            # Add explanation
            st.markdown("""
            This chart shows how categories are distributed across different sections of the profit and loss report.
            It helps identify which categories contribute most to income, costs, and expenses.
            """)
        except Exception as e:
            logger.error(f"Error creating category comparison chart: {str(e)}")
            logger.error(traceback.format_exc())
            st.error("Error creating category comparison chart. Please check the logs for details.")
