"""
Profitability Analysis Dashboard.

This module provides a Streamlit-based dashboard for analyzing
profit and loss reports and visualizing financial performance.
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import traceback
from pathlib import Path

# Import core analyzer and validation
from src.core.analyzer import analyze_profit_loss
from src.core.validation import validate_excel_file, ExcelFileValidationError

# Import dashboard modules
from src.dashboard.utils import calculate_financial_ratios, get_top_accounts
from src.dashboard.visualizations.charts import (
    create_profit_breakdown_chart,
    create_expense_breakdown_chart
)
from src.dashboard.components.ui import (
    render_header,
    render_kpi_metrics,
    render_financial_summary,
    render_detailed_sections,
    render_export_options,
    render_insights
)
from src.dashboard.components.category_ui import render_category_analysis

# Set page configuration
st.set_page_config(
    page_title="Profitability Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: white !important;
        border-radius: 5px !important;
        padding: 1rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main entry point for the Streamlit dashboard."""
    # Header
    st.markdown("<div class='main-header'>Profitability Analysis Dashboard</div>", unsafe_allow_html=True)
    st.markdown("Upload a Profit & Loss Excel file to analyze financial performance and visualize key metrics.")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Upload P&L Report")
        uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
        
        # Add help text about expected file format
        with st.expander("ℹ️ About P&L Reports"):
            st.markdown("""
            **Expected File Format:**
            - Excel file (.xlsx or .xls)
            - Contains income/revenue section
            - Contains expense section
            - Contains profit calculations
            - Has numeric financial data
            
            **Common Issues:**
            - Missing section headers
            - Too many empty cells
            - No financial data
            - Incorrect file format
            """)
        
        st.markdown("---")
        st.markdown("### Options")
        show_accounts = st.checkbox("Show detailed accounts", value=True)
        chart_type = st.selectbox(
            "Chart type for expense breakdown", 
            ["Pie Chart", "Treemap", "Bar Chart"],
            index=0
        )
        show_categories = st.checkbox("Show category analysis", value=True)
        show_insights = st.checkbox("Show financial insights", value=True)
        
        # Add option for using LLM-powered insights
        use_llm = False
        if show_insights:
            use_llm = st.checkbox("Enable AI-powered financial insights", value=True, 
                                help="Uses OpenAI to generate personalized financial insights and recommendations.")
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This dashboard analyzes profit and loss reports to provide financial insights.
        
        **Features:**
        - Financial KPI calculation
        - Expense breakdown visualization
        - Detailed account analysis
        - Financial insights and recommendations
        """)
    
    # Main content
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        temp_file_path = os.path.join(os.getcwd(), "temp_upload.xlsx")
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Validate and analyze the profit and loss report
        with st.spinner("Validating and analyzing profit and loss report..."):
            try:
                # First validate the file
                validation_result = validate_excel_file(temp_file_path)
                
                # Show warnings if any
                if validation_result.warnings:
                    st.warning("⚠️ **Validation Warnings:**")
                    for warning in validation_result.warnings:
                        st.warning(f"- {warning}")
                
                # If validation fails, show detailed errors
                if not validation_result.is_valid:
                    st.error("❌ **File Validation Failed**")
                    for error in validation_result.errors:
                        st.error(f"- {error}")
                    st.info("Please upload a valid Profit & Loss Excel report. The file should contain financial data with income, expenses, and profit sections.")
                    return
                
                # If validation passes, analyze the file
                result = analyze_profit_loss(temp_file_path)
                
                # Save the result to a JSON file
                output_path = os.path.join(os.getcwd(), "profit_loss_analysis.json")
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                
                # Display the analysis
                display_analysis(result, show_accounts, chart_type, show_categories, show_insights, use_llm)
                
            except ExcelFileValidationError as e:
                st.error(f"❌ **Validation Error:** {str(e)}")
                st.info("Please upload a valid Profit & Loss Excel report. The file should contain financial data with income, expenses, and profit sections.")
            except Exception as e:
                st.error(f"❌ **Error analyzing the file:** {str(e)}")
                st.error("An unexpected error occurred during analysis.")
                st.code(traceback.format_exc(), language="python")
                st.info("If this error persists, please check the log files or contact support.")
        
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    else:
        # Display sample data or instructions
        st.info("👈 Please upload a Profit & Loss Excel file to get started.")
        
        # Instructions for valid P&L reports
        st.markdown("### How to Prepare Your P&L Report")
        st.markdown("""
        For best results, ensure your Profit & Loss report includes:
        
        1. **Clear Section Headers** - Income/Revenue, Expenses, Profit sections should be clearly labeled
        2. **Account Details** - Individual line items with account names and values
        3. **Financial Totals** - Section totals and profit calculations
        4. **Consistent Format** - Standard Excel format without merged cells or complex formatting
        
        The dashboard will automatically validate your file before processing.
        """)
        
        # Sample image or placeholder
        st.markdown("### Sample Dashboard Preview")
        st.image("https://via.placeholder.com/800x400?text=Profit+and+Loss+Analysis+Dashboard", 
                 caption="Upload a file to see your actual data analysis")


def display_analysis(data, show_accounts, chart_type, show_categories, show_insights, use_llm=True):
    """
    Display the profit and loss analysis with visualizations.
    
    Args:
        data: The profit and loss data dictionary.
        show_accounts: Whether to show detailed account information.
        chart_type: Type of chart to use for expense breakdown.
        show_categories: Whether to show category analysis.
        show_insights: Whether to show financial insights.
        use_llm: Whether to use LLM for generating insights.
    """
    # Company info section
    render_header(data)
    
    # Financial metrics section
    render_kpi_metrics(data)
    
    # Financial summary section
    render_financial_summary(data, chart_type)
    
    # Category analysis section (optional)
    if show_categories:
        render_category_analysis(data)
    
    # Financial insights section (optional)
    if show_insights:
        render_insights(data, use_llm=use_llm)
    
    # Detailed sections (optional)
    if show_accounts:
        render_detailed_sections(data)
    
    # Export options
    render_export_options(data)


if __name__ == "__main__":
    main()