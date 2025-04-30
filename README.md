# Profitability Analysis Agent

A Python-based tool for analyzing profit and loss reports from Excel files, converting them to structured JSON format, and visualizing the results through an interactive Streamlit dashboard.

## Features

### Data Processing
- Extract company name, period, and basis type from P&L reports
- Identify all sections in the report (Trading Income, Cost of Sales, Gross Profit, etc.)
- Extract account details with codes when available
- Calculate section totals with fallback mechanisms
- Output standardized JSON structure
- Handle various report formats (complete, partial)
- Validate and correct inconsistent totals

### Interactive Dashboard
- Upload and analyze P&L reports through a user-friendly interface
- View key financial metrics and KPIs (gross margin, net margin, expense ratios)
- Visualize profit breakdown and expense distribution
- Explore detailed account information in an organized format
- Generate financial insights and recommendations (rule-based and AI-powered)
- Export analysis results in JSON or CSV format

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Profitability_Analysis_Agent.git
cd Profitability_Analysis_Agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up OpenAI API key (for AI-powered insights):
   - Create a `.env` file in the root directory based on `.env.example`
   - Add your OpenAI API key to the `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL_NAME=gpt-4o-mini  # or another supported model
   ```

## Usage

### Unified Entry Point

The application now has a single entry point that supports both CLI and dashboard modes:

```bash
# Launch the dashboard (default)
python app.py

# Analyze a specific file via CLI
python app.py path/to/your/excel_file.xlsx

# Analyze a file and specify output location
python app.py path/to/your/excel_file.xlsx -o path/to/output.json

# Explicitly launch the dashboard
python app.py --dashboard
```

### Using as a Library

```python
from src.core.analyzer import analyze_profit_loss

# Analyze a profit and loss report
result = analyze_profit_loss("path/to/your/excel_file.xlsx")

# Print the result
import json
print(json.dumps(result, indent=2))
```

## AI-Powered Financial Insights

The dashboard now features AI-powered financial insights and recommendations using OpenAI's language models. This feature:

- Analyzes your financial data to generate personalized insights
- Provides actionable recommendations based on your specific financial situation
- Highlights strengths, weaknesses, and opportunities in your financial performance
- Offers detailed explanations with expected impact and implementation difficulty

### Using AI Insights

1. Upload your P&L report in the dashboard
2. Ensure "Show financial insights" is checked in the options
3. Toggle "Enable AI-powered financial insights" to use the LLM for analysis
4. View the generated insights and recommendations
5. Provide feedback on the quality of insights using the buttons provided

### Privacy Considerations

When using the AI-powered insights feature:

- Your financial data is sent to OpenAI's API for analysis
- No data is permanently stored on OpenAI's servers
- For maximum privacy, you can disable the AI-powered insights and use the built-in rule-based insights instead
- All API calls are made with your own API key, giving you full control over usage and billing

## Output Format

The tool produces a structured JSON output with the following format:

```json
{
  "companyName": "Company Name",
  "period": "Period (e.g., January 2025)",
  "basisType": "Accrual or Cash",
  "reportType": "Complete or Partial",
  "sections": {
    "tradingIncome": {
      "accounts": [
        {
          "code": "Optional account code",
          "name": "Account name",
          "value": 1000
        }
      ],
      "total": 1000
    },
    "costOfSales": {
      "accounts": [...],
      "total": 500
    },
    "grossProfit": 500,
    "operatingExpenses": {
      "accounts": [...],
      "total": 300
    },
    "netProfit": 200
  }
}
```

## Testing

The project includes comprehensive unit tests for all functionality. To run the tests:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.

# Run specific test file
pytest tests/test_analyze_profit_loss.py
```

## Project Structure

The project has been reorganized into a more modular structure:

```
profitability_analysis_agent/
├── src/                      # Source code directory
│   ├── core/                 # Core analysis functionality
│   │   ├── analyzer.py       # Main analysis logic
│   │   └── models/           # Data models (future use)
│   ├── dashboard/            # Dashboard components
│   │   ├── app.py            # Streamlit dashboard entry point
│   │   ├── utils.py          # Dashboard utility functions
│   │   ├── components/       # UI components
│   │   │   └── ui.py         # Reusable UI elements
│   │   └── visualizations/   # Chart creation
│   │       └── charts.py     # Visualization functions
│   └── utils/                # Common utilities
│       └── helpers.py        # Shared helper functions
├── tests/                    # Test directory
│   └── ...                   # Test files
├── test_files/               # Sample files for testing
│   └── ...                   # Test Excel files
├── app.py                    # Unified entry point
├── requirements.txt          # Project dependencies
├── README.md                 # Project documentation
├── PLANNING.md               # Implementation plan
└── TASK.md                   # Task tracking
```

## Development

### Adding New Features

1. Update the appropriate module with new functionality
2. Add unit tests for the new feature
3. Update documentation as needed
4. Run tests to ensure everything works correctly

### Coding Standards

- Follow PEP8 standards
- Use type hints
- Format code with `black`
- Use `pydantic` for data validation
- Write Google-style docstrings for all functions
- All new features require Pytest unit tests
- Maximum file length of 500 lines (split into modules if needed)