"""
Profitability Analysis Agent - Main Entry Point

This module serves as the unified entry point for the Profitability Analysis Agent,
providing both command-line and dashboard functionality.

Usage:
    - Run without arguments to launch the Streamlit dashboard
    - Run with a file path argument to analyze a specific P&L report via CLI
    - Use --help to see all available options
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Add src to the Python path
sys.path.append(str(Path(__file__).parent))

# Import core functionality
from src.core.analyzer import analyze_profit_loss
from src.utils.helpers import save_json_file


def analyze_file(file_path, output_path=None):
    """
    Analyze a profit and loss report file and save the results.
    
    Args:
        file_path: Path to the Excel file to analyze.
        output_path: Path to save the JSON output (optional).
        
    Returns:
        The analysis result dictionary.
    """
    # Validate file path
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
    
    # Analyze the profit and loss report
    try:
        result = analyze_profit_loss(file_path)
        
        # Determine output path if not specified
        if not output_path:
            output_path = os.path.join(os.path.dirname(file_path), 'profit_loss_analysis.json')
        
        # Save the result to a JSON file
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nAnalysis saved to {output_path}")
        return result
    
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        sys.exit(1)


def run_dashboard():
    """
    Launch the Streamlit dashboard.
    """
    # Path to the dashboard app
    dashboard_path = os.path.join(os.path.dirname(__file__), "src", "dashboard", "app.py")
    
    # Check if the dashboard app exists
    if not os.path.exists(dashboard_path):
        print(f"Error: Dashboard app not found at {dashboard_path}")
        sys.exit(1)
    
    # Check if Streamlit is installed
    try:
        import streamlit
        print("Starting Profitability Analysis Dashboard...")
    except ImportError:
        print("Streamlit is not installed. Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Run the Streamlit app
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])


def main():
    """
    Main entry point for the application.
    """
    parser = argparse.ArgumentParser(
        description="Profitability Analysis Agent - Analyze profit and loss reports"
    )
    
    parser.add_argument(
        "file_path", 
        nargs="?", 
        help="Path to the Excel file to analyze (if not provided, launches the dashboard)"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Path to save the JSON output (default: same directory as input file)"
    )
    
    parser.add_argument(
        "-d", "--dashboard", 
        action="store_true",
        help="Launch the Streamlit dashboard"
    )
    
    args = parser.parse_args()
    
    # Determine which mode to run
    if args.dashboard or args.file_path is None:
        # Run in dashboard mode
        run_dashboard()
    else:
        # Run in CLI mode
        analyze_file(args.file_path, args.output)


if __name__ == "__main__":
    main()