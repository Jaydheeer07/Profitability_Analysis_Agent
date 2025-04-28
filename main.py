from analyze_profit_loss import analyze_profit_loss
import os
import json
import pandas as pd

def main():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Excel file
    file_path = os.path.join(script_dir, 'test_files', 'Tasman_Agri_Pty_Ltd_-_Profit_and_Loss.xlsx')
    
    # Analyze the profit and loss report
    result = analyze_profit_loss(file_path)
    
    # Print the result as formatted JSON
    print(json.dumps(result, indent=2))
    
    # Save the result to a JSON file
    output_path = os.path.join(script_dir, 'profit_loss_analysis.json')
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nAnalysis saved to {output_path}")

if __name__ == "__main__":
    main()
