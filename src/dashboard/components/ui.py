"""
UI components for the Profitability Analysis Dashboard.

This module contains reusable UI components for the Streamlit dashboard,
helping to keep the main app.py file clean and modular.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from typing import Dict, List, Any, Optional

# These imports will be updated after all files are moved
from src.dashboard.utils import calculate_financial_ratios, get_top_accounts, format_currency
from src.utils.categorization import get_accounts_by_category, get_category_totals
from src.dashboard.visualizations.charts import (
    create_profit_breakdown_chart,
    create_expense_breakdown_chart,
    create_income_breakdown_chart,
    create_financial_metrics_gauge,
    create_financial_summary_table
)


def render_header(data: Dict[str, Any]) -> None:
    """
    Render the header section with company information.
    
    Args:
        data: The profit and loss data dictionary.
    """
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Company:** {data.get('companyName', 'N/A')}")
    with col2:
        st.markdown(f"**Period:** {data.get('period', 'N/A')}")
    with col3:
        st.markdown(f"**Basis:** {data.get('basisType', 'N/A')} | **Type:** {data.get('reportType', 'N/A')}")
    
    st.markdown("---")


def render_kpi_metrics(data: Dict[str, Any]) -> None:
    """
    Render the KPI metrics section.
    
    Args:
        data: The profit and loss data dictionary.
    """
    st.markdown("<div class='section-header'>Financial KPIs</div>", unsafe_allow_html=True)
    
    # Calculate financial ratios
    ratios = calculate_financial_ratios(data)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gross Profit Margin", f"{ratios['gross_margin']:.1f}%")
    with col2:
        st.metric("Net Profit Margin", f"{ratios['net_margin']:.1f}%")
    with col3:
        st.metric("Expense Ratio", f"{ratios['expense_ratio']:.1f}%")
    with col4:
        st.metric("COGS Ratio", f"{ratios['cogs_ratio']:.1f}%")


def render_financial_summary(data: Dict[str, Any], chart_type: str) -> None:
    """
    Render the financial summary section with charts.
    
    Args:
        data: The profit and loss data dictionary.
        chart_type: Type of chart to use for expense breakdown.
    """
    st.markdown("<div class='section-header'>Financial Summary</div>", unsafe_allow_html=True)
    
    # Get sections data
    sections = data.get('sections', {})
    
    # Create columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Profit Breakdown")
        
        # Create profit breakdown chart
        fig = create_profit_breakdown_chart(data)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Expense Breakdown")
        
        # Create expense breakdown chart based on selected type
        if 'operatingExpenses' in sections and 'accounts' in sections['operatingExpenses']:
            fig = create_expense_breakdown_chart(
                sections['operatingExpenses']['accounts'],
                chart_type=chart_type
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No operating expense data available.")
    
    # Additional charts in expandable sections
    with st.expander("Income Breakdown", expanded=False):
        if 'tradingIncome' in sections and 'accounts' in sections['tradingIncome']:
            fig = create_income_breakdown_chart(sections['tradingIncome']['accounts'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trading income data available.")
    
    with st.expander("Financial Metrics", expanded=False):
        # Calculate financial ratios
        ratios = calculate_financial_ratios(data)
        
        # Create gauge chart for key metrics
        fig = create_financial_metrics_gauge(ratios)
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Financial Summary Table", expanded=False):
        # Create summary table
        fig = create_financial_summary_table(data)
        st.plotly_chart(fig, use_container_width=True)


def render_category_analysis(data: Dict[str, Any]) -> None:
    """
    Render category-based analysis of accounts.
    
    Args:
        data: The profit and loss data dictionary.
    """
    st.markdown("<div class='section-header'>Category Analysis</div>", unsafe_allow_html=True)
    
    # Get category totals for each section
    tabs = st.tabs(["All Categories", "Income Categories", "Cost Categories", "Expense Categories"])
    
    with tabs[0]:
        # All categories across sections
        category_totals = get_category_totals(data)
        
        if category_totals:
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
            
            # Create pie chart
            fig = px.pie(
                df, 
                names='Category', 
                values=df.index,  # Using index as placeholder since we can't use formatted currency
                title='Distribution by Category',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available.")
    
    with tabs[1]:
        # Income categories
        income_categories = get_category_totals(data, 'tradingIncome')
        
        if income_categories:
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
        else:
            st.info("No income category data available.")
    
    with tabs[2]:
        # Cost categories
        cost_categories = get_category_totals(data, 'costOfSales')
        
        if cost_categories:
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
        else:
            st.info("No cost category data available.")
    
    with tabs[3]:
        # Expense categories
        expense_categories = get_category_totals(data, 'operatingExpenses')
        
        if expense_categories:
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
        else:
            st.info("No expense category data available.")


def render_detailed_sections(data: Dict[str, Any]) -> None:
    """
    Render detailed sections with account-level information.
    
    Args:
        data: The profit and loss data dictionary.
    """
    st.markdown("<div class='section-header'>Detailed Accounts</div>", unsafe_allow_html=True)
    
    # Get sections data
    sections = data.get('sections', {})
    
    # Trading Income section
    with st.expander("Trading Income", expanded=False):
        if 'tradingIncome' in sections and 'accounts' in sections['tradingIncome']:
            accounts = sections['tradingIncome']['accounts']
            total = sections['tradingIncome']['total']
            
            # Create DataFrame for display
            df = pd.DataFrame(accounts)
            if not df.empty:
                # Add percentage column
                df['percentage'] = (df['value'] / total * 100).round(1)
                df['percentage'] = df['percentage'].apply(lambda x: f"{x}%")
                
                # Format value column
                df['value'] = df['value'].apply(format_currency)
                
                # Rename columns for display
                df = df.rename(columns={
                    'name': 'Account Name',
                    'code': 'Account Code',
                    'value': 'Amount',
                    'percentage': 'Percentage',
                    'category': 'Category'
                })
                
                # Display the data
                st.dataframe(df, use_container_width=True)
                st.markdown(f"**Total Trading Income:** {format_currency(total)}")
            else:
                st.info("No trading income accounts available.")
        else:
            st.info("No trading income data available.")
    
    # Cost of Sales section
    with st.expander("Cost of Sales", expanded=False):
        if 'costOfSales' in sections and 'accounts' in sections['costOfSales']:
            accounts = sections['costOfSales']['accounts']
            total = sections['costOfSales']['total']
            
            # Create DataFrame for display
            df = pd.DataFrame(accounts)
            if not df.empty:
                # Add percentage column
                df['percentage'] = (df['value'].abs() / abs(total) * 100).round(1)
                df['percentage'] = df['percentage'].apply(lambda x: f"{x}%")
                
                # Format value column
                df['value'] = df['value'].apply(format_currency)
                
                # Rename columns for display
                df = df.rename(columns={
                    'name': 'Account Name',
                    'code': 'Account Code',
                    'value': 'Amount',
                    'percentage': 'Percentage'
                })
                
                # Display the data
                st.dataframe(df, use_container_width=True)
                st.markdown(f"**Total Cost of Sales:** {format_currency(total)}")
            else:
                st.info("No cost of sales accounts available.")
        else:
            st.info("No cost of sales data available.")
    
    # Operating Expenses section
    with st.expander("Operating Expenses", expanded=False):
        if 'operatingExpenses' in sections and 'accounts' in sections['operatingExpenses']:
            accounts = sections['operatingExpenses']['accounts']
            total = sections['operatingExpenses']['total']
            
            # Create DataFrame for display
            df = pd.DataFrame(accounts)
            if not df.empty:
                # Add percentage column
                df['percentage'] = (df['value'].abs() / abs(total) * 100).round(1)
                df['percentage'] = df['percentage'].apply(lambda x: f"{x}%")
                
                # Format value column
                df['value'] = df['value'].apply(format_currency)
                
                # Rename columns for display
                df = df.rename(columns={
                    'name': 'Account Name',
                    'code': 'Account Code',
                    'value': 'Amount',
                    'percentage': 'Percentage'
                })
                
                # Sort by absolute value (descending)
                if 'Amount' in df.columns:
                    df = df.sort_values(by='Percentage', ascending=False)
                
                # Display the data
                st.dataframe(df, use_container_width=True)
                st.markdown(f"**Total Operating Expenses:** {format_currency(total)}")
            else:
                st.info("No operating expense accounts available.")
        else:
            st.info("No operating expense data available.")


def render_export_options(data: Dict[str, Any]) -> None:
    """
    Render export options for the data.
    
    Args:
        data: The profit and loss data dictionary.
    """
    st.markdown("<div class='section-header'>Export Options</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export as JSON
        json_data = json.dumps(data, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name="profit_loss_analysis.json",
            mime="application/json"
        )
    
    with col2:
        # Export as CSV
        sections = data.get('sections', {})
        
        # Combine all accounts into a single DataFrame
        all_accounts = []
        
        if 'tradingIncome' in sections and 'accounts' in sections['tradingIncome']:
            for account in sections['tradingIncome']['accounts']:
                account['section'] = 'Trading Income'
                all_accounts.append(account)
        
        if 'costOfSales' in sections and 'accounts' in sections['costOfSales']:
            for account in sections['costOfSales']['accounts']:
                account['section'] = 'Cost of Sales'
                all_accounts.append(account)
        
        if 'operatingExpenses' in sections and 'accounts' in sections['operatingExpenses']:
            for account in sections['operatingExpenses']['accounts']:
                account['section'] = 'Operating Expenses'
                all_accounts.append(account)
        
        if all_accounts:
            df = pd.DataFrame(all_accounts)
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="profit_loss_accounts.csv",
                mime="text/csv"
            )
        else:
            st.button("Download CSV", disabled=True)


def render_insights(data: Dict[str, Any], use_llm: bool = True) -> None:
    """
    Render financial insights based on the data.
    
    Args:
        data: The profit and loss data dictionary.
        use_llm: Whether to use the LLM for generating insights.
    """
    from src.utils.insights_helper import generate_llm_insights, format_insight_for_display, format_recommendation_for_display
    import time
    
    st.markdown("<div class='section-header'>Financial Insights</div>", unsafe_allow_html=True)
    
    with st.expander("Financial Insights & Recommendations", expanded=True):
        # Get sections data
        sections = data.get('sections', {})
        
        # Calculate financial ratios
        ratios = calculate_financial_ratios(data)
        
        # Toggle for LLM vs. rule-based insights
        col1, col2 = st.columns([3, 1])
        with col2:
            use_llm_toggle = st.checkbox("Use AI-powered insights", value=use_llm)
        
        # Display a loading indicator while generating LLM insights
        if use_llm_toggle:
            with st.spinner("Generating AI-powered financial insights..."):
                llm_response = generate_llm_insights(data, use_llm=use_llm_toggle)
                
                if llm_response:
                    # Display LLM-generated insights
                    st.markdown("### Key Insights")
                    st.markdown(f"*AI-powered analysis based on your financial data*")
                    
                    # Display executive summary
                    st.info(llm_response.summary)
                    
                    # Display insights
                    for insight in llm_response.insights:
                        st.markdown(format_insight_for_display(insight.dict()))
                    
                    # Display recommendations
                    st.markdown("### Recommendations")
                    for recommendation in llm_response.recommendations:
                        st.markdown(format_recommendation_for_display(recommendation.dict()))
                    
                    # Display generation metadata
                    st.markdown("---")
                    st.caption(f"Insights generated at {llm_response.generated_at.strftime('%Y-%m-%d %H:%M')} using {llm_response.llm_model}")
                    
                    # Add feedback mechanism
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("👍 Helpful"):
                            st.success("Thank you for your feedback!")
                    with col2:
                        if st.button("👎 Not helpful"):
                            st.success("Thank you for your feedback!")
                    with col3:
                        if st.button("🔄 Regenerate"):
                            st.experimental_rerun()
                    
                    return  # Exit function after displaying LLM insights
                else:
                    st.error("Failed to generate AI-powered insights. Falling back to rule-based insights.")
        
        # If LLM is not used or failed, use rule-based insights
        st.markdown("### Key Insights")
        if not use_llm_toggle:
            st.markdown("*Using rule-based analysis*")
        
        # Generate rule-based insights
        insights = []
        
        # Gross profit insights
        if ratios['gross_margin'] > 40:
            insights.append("✅ **Strong Gross Margin**: Your gross profit margin is above 40%, which is excellent for most industries.")
        elif ratios['gross_margin'] < 20:
            insights.append("⚠️ **Low Gross Margin**: Your gross profit margin is below 20%, which may indicate pricing challenges or high cost of goods sold.")
        
        if ratios['net_margin'] > 15:
            insights.append("✅ **Excellent Net Margin**: Your net profit margin is above 15%, which is excellent for most industries.")
        elif ratios['net_margin'] < 5:
            insights.append("⚠️ **Low Net Margin**: Your net profit margin is below 5%, indicating potential issues with overall profitability.")
        
        # Expense insights
        if ratios['expense_ratio'] > 40:
            insights.append("⚠️ **High Operating Expenses**: Your operating expenses represent over 40% of revenue, which may be worth reviewing for optimization opportunities.")
        
        # Top expense insight
        if 'operatingExpenses' in sections and 'accounts' in sections['operatingExpenses']:
            expense_accounts = sections['operatingExpenses']['accounts']
            if expense_accounts:
                df = pd.DataFrame(expense_accounts)
                top_expense = df.loc[df['value'].abs().idxmax()]
                insights.append(f"📊 **Largest Expense**: Your largest expense category is '{top_expense['name']}' at {format_currency(top_expense['value'])}, representing {abs(top_expense['value'])/sections['operatingExpenses']['total']*100:.1f}% of total operating expenses.")
        
        # Display insights
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.info("No significant insights detected in the current data.")
        
        # Recommendations section
        st.markdown("### Recommendations")
        st.markdown("""
        Based on the financial analysis, consider:
        
        1. Regular monitoring of your gross profit margin and cost of sales
        2. Reviewing operating expenses for optimization opportunities
        3. Tracking your net profit margin over time to identify trends
        """)