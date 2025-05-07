# FinOps360 Cost Analysis Dashboard

A comprehensive cloud cost analysis tool with environment cost breakdowns, trend analysis, and forecasting capabilities. The system analyzes both Production and Non-Production costs with percentage breakdowns and provides detailed visualizations.

## Features

- **Unified Environment Dashboard**: View PROD and NON-PROD costs together with percentage calculations
- **Trend Analysis**: Track daily and monthly cost trends with historical comparisons
- **Fiscal Year Comparisons**: Compare costs across different fiscal years (FY24, FY25, FY26)
- **Forecasting**: Predict future costs based on historical patterns and growth trends
- **Product Analysis**: View costs by product ID with Production/Non-Production breakdown
- **Average Daily Cost Metrics**: Analyze cost data using average daily spend rather than raw totals
- **Interactive HTML Reports**: Generate detailed HTML reports with interactive charts and tables

## Quick Start

Run the entire system with a single command:

```bash
bash run.sh
```

This script will:
1. Check if required data exists, generating it if needed
2. Check for BigQuery availability and authenticate if possible
3. Load data to BigQuery tables if available
4. Create necessary BigQuery views
5. Generate the HTML dashboard

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Configure your BigQuery settings in `config.yaml`:
```yaml
bigquery:
  project_id: your-project-id
  dataset: your-dataset
  table: cost_analysis_new
  avg_table: avg_daily_cost_table
  use_bigquery: true
```

3. Set up your BigQuery credentials (if needed):
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Project Structure

The application has been streamlined with a clean architecture:

- `app/`: Main application code
  - `main.py`: Primary entry point
  - `dashboard.py`: Dashboard generation logic
  - `data_access.py`: BigQuery data access functions
  - `data/`: Schema definitions and SQL scripts
  - `templates/`: HTML templates for the dashboard
  - `utils/`: Utility modules for configuration, BigQuery access, and chart generation
- `reports/`: Generated HTML reports
- `run.sh`: Main script to run the application

## Usage

### Generate HTML Dashboard

```bash
python -m app.main
```

Options:
- `--output`: Output HTML file path (default: reports/finops_dashboard.html)
- `--config`: Path to config file (default: config.yaml)
- `--template`: Path to HTML template (default: app/templates/dashboard_template.html)

## BigQuery Integration

For detailed instructions on integrating with your own BigQuery data sources, see [BIGQUERY_INTEGRATION.md](BIGQUERY_INTEGRATION.md).

## License

© 2025 FinOps360