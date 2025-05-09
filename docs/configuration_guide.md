# FinOps360 Configuration Guide

This document provides information on configuring the FinOps360 Cost Analysis Dashboard, including how to add or modify data sources.

## Configuration Files

The main configuration files for the application are:

- `app/utils/config.py` - Contains the base configuration class and loading functions
- `config.yaml` - YAML configuration file with dashboard settings

## Adding a New Data Source

To add a new data source (like a new BigQuery table), follow these steps:

1. Create a new SQL query file in the `app/sql/` directory
2. Add the data source configuration to `config.yaml` if needed
3. Add a new function in `app/data_access.py` to retrieve the data
4. Add sample data generation in `app/utils/sample_data.py`
5. Update the dashboard generation in `app/dashboard.py`

## Modifying Query Parameters

The query parameters are set in `app/data_access.py` and passed to the SQL queries. To modify these:

1. Locate the function in `app/data_access.py` for the specific query
2. Update the parameters in the function
3. Make sure the SQL query in `app/sql/` accepts the new parameters

## Chart Configuration

Chart configurations are defined in `app/utils/chart_config.py`. The main components:

- `CHART_COLORS` - Colors used for different data series
- `CHART_CONFIGS` - Configuration for each chart type
- `are_charts_enabled()` - Function to determine if interactive charts are enabled

## Adding a New Chart

To add a new chart to the dashboard:

1. Create a new chart generation function in `app/utils/interactive_charts.py`
2. Add chart configuration to `CHART_CONFIGS` in `app/utils/chart_config.py`
3. Update `app/dashboard.py` to call your new chart function
4. Add the chart to the HTML template in `app/templates/dashboard_template.html`

## Environment Variables

The application uses the following environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Cloud credentials file
- `BQ_PROJECT_ID` - BigQuery project ID
- `BQ_DATASET` - BigQuery dataset name
- `BQ_COST_TABLE` - BigQuery cost analysis table name
- `BQ_AVG_TABLE` - BigQuery average daily cost table name

These can be set in your shell or in a `.env` file.

## Dashboard Layout Configuration

The dashboard layout is controlled by `app/templates/dashboard_template.html`. Key sections:

- CSS styles at the top
- Main container with scorecards
- Chart sections
- Table sections

## Date Range Configuration

Date ranges for comparisons are configured in `config.yaml` under the `data` section:

```yaml
data:
  day_current_date: '2025-05-03'
  day_previous_date: '2025-05-02'
  week_current_start: '2025-04-27'
  week_current_end: '2025-05-03'
  week_previous_start: '2025-04-20'
  week_previous_end: '2025-04-26'
  month_current: '2025-04'
  month_previous: '2025-03'
  top_products_count: 10
  nonprod_percentage_threshold: 30
  display_millions: true
```

Modify these values to change the comparison date ranges.