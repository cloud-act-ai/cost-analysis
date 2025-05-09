# FinOps360 Cost Analysis Dashboard Documentation

This directory contains documentation for the FinOps360 Cost Analysis Dashboard.

## Available Documentation

- [FY25 Budget Integration Guide](./fy25_budget_integration.md) - Instructions for integrating FY25 budget data from a new table
- [Daily Cost Chart Editing Guide](./daily_cost_chart_editing.md) - How to edit, add, or remove lines from the daily cost chart

## Project Structure

The FinOps360 Cost Analysis Dashboard is structured as follows:

- `/app` - Main application code
  - `/app/data` - Sample data files and schemas
  - `/app/sql` - SQL query files
  - `/app/templates` - HTML templates
  - `/app/utils` - Utility functions and configuration
- `/reports` - Generated dashboard reports
- `/docs` - Documentation (you are here)

## Key Files

- `app/main.py` - Entry point for the application
- `app/dashboard.py` - Dashboard generation logic
- `app/data_access.py` - Data retrieval from BigQuery
- `app/utils/interactive_charts.py` - Chart generation code
- `app/utils/chart_config.py` - Chart configuration
- `app/utils/sample_data.py` - Sample data generation
- `app/templates/dashboard_template.html` - HTML template for the dashboard

## Common Tasks

- **Running the dashboard**: `./run.sh` or `python -m app.main`
- **Updating SQL queries**: Edit files in `/app/sql/`
- **Modifying chart appearance**: Edit `/app/utils/chart_config.py`
- **Changing data calculations**: Edit `/app/dashboard.py`
- **Modifying HTML layout**: Edit `/app/templates/dashboard_template.html`

## Adding New Features

When adding new features to the dashboard:

1. Add any new SQL queries to the `/app/sql/` directory
2. Add functions to retrieve the data in `/app/data_access.py`
3. Add sample data generation in `/app/utils/sample_data.py`
4. Update the dashboard generation in `/app/dashboard.py`
5. Update the HTML template in `/app/templates/dashboard_template.html`
6. Add chart configurations in `/app/utils/chart_config.py` if needed

See specific feature guides for more detailed instructions.