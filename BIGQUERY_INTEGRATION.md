# BigQuery Integration Guide for FinOps360 Cost Analysis Dashboard

This guide explains how to connect the FinOps360 dashboard to your own BigQuery data sources.

## Overview

The dashboard is designed to work with two main tables:

1. **cost_analysis_new**: Raw cost data for cloud resources 
2. **avg_daily_cost_table**: Aggregated cost data for trend analysis and forecasting

## Schema Requirements

### cost_analysis_new Schema

Your primary cost table needs these columns:

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| date | DATE | Date of the cost record |
| cto | STRING | CTO/Tech leadership organization |
| cloud | STRING | Cloud provider (AWS, Azure, GCP) |
| tr_product_pillar_team | STRING | Product pillar team |
| tr_subpillar_name | STRING | Sub-pillar name (optional) |
| tr_product_id | STRING | Product ID |
| tr_product | STRING | Product name |
| managed_service | STRING | Cloud managed service |
| environment | STRING | Environment type (must contain "PROD" for production, any other value is treated as non-production) |
| cost | FLOAT | Daily cost amount in USD |

### avg_daily_cost_table Schema

This table/view can be generated from the main cost data with this schema:

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| date | DATE | Date of the record |
| environment_type | STRING | "PROD" or "NON-PROD" |
| cto | STRING | CTO/Tech leadership organization |
| fy24_avg_daily_spend | FLOAT | FY24 average daily spend |
| fy25_avg_daily_spend | FLOAT | FY25 average daily spend |
| fy26_ytd_avg_daily_spend | FLOAT | FY26 year-to-date average daily spend |
| fy26_forecasted_avg_daily_spend | FLOAT | FY26 forecasted average daily spend |
| fy26_avg_daily_spend | FLOAT | FY26 total average daily spend |
| daily_cost | FLOAT | Current daily cost |

## Configuration

1. Update `config.yaml` with your BigQuery settings:

```yaml
bigquery:
  project_id: "your-project-id"
  dataset: "your-dataset"
  table: "your-cost-table"
  avg_table: "your-avg-daily-cost-table"
  use_bigquery: true
  credentials: "/path/to/credentials.json"  # Optional
```

2. Set up authentication:

Option 1: Environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

Option 2: Specify in config.yaml as shown above

## Creating Tables/Views from Your Data

### Option 1: Use Existing Tables

If you already have tables with the required schema, simply update the `config.yaml` file to point to them.

### Option 2: Create New Tables From Your Data Source

1. Create the cost_analysis_new table with the schema in `data/cost_analysis_schema.json`
2. Load your source data with appropriate transformations to match the schema

### Option 3: Create the avg_daily_cost_table View

Use the SQL query in `data/create_avg_daily_view.sql` as a template, modifying as needed for your data structure.

## SQL for Creating avg_daily_cost_table 

This query creates the avg_daily_cost_table view:

```sql
CREATE OR REPLACE VIEW `your-project-id.your-dataset.avg_daily_cost_table` AS
WITH fiscal_year_averages AS (
    SELECT 
        CASE 
            WHEN environment LIKE 'PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        cto,
        -- FY24 Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2023-02-01' AND '2024-01-31' THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2023-02-01' AND '2024-01-31' THEN date ELSE NULL END), 0), 2) AS fy24_avg_daily_spend,
        -- FY25 Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2024-02-01' AND '2025-01-31' THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2024-02-01' AND '2025-01-31' THEN date ELSE NULL END), 0), 2) AS fy25_avg_daily_spend,
        -- FY26 YTD Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN date ELSE NULL END), 0), 2) AS fy26_ytd_avg_daily_spend,
        -- FY26 Forecasted Average Daily Spend
        ROUND(
            (SUM(CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN cost ELSE 0 END) / 
            NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN date ELSE NULL END), 0)) * 1.15, 
            2) AS fy26_forecasted_avg_daily_spend,
        -- FY26 Total Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2025-02-01' AND '2026-01-31' THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND '2026-01-31' THEN date ELSE NULL END), 0), 2) AS fy26_avg_daily_spend
    FROM `your-project-id.your-dataset.cost_analysis_new`
    WHERE date BETWEEN '2023-02-01' AND '2026-01-31'
    GROUP BY environment_type, cto
),
daily_costs AS (
    SELECT 
        date,
        CASE 
            WHEN environment LIKE 'PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        cto,
        ROUND(SUM(cost), 2) AS daily_cost
    FROM `your-project-id.your-dataset.cost_analysis_new`
    WHERE date BETWEEN '2023-02-01' AND '2026-01-31'
    GROUP BY date, environment_type, cto
)
SELECT 
    d.date,
    d.environment_type,
    d.cto,
    f.fy24_avg_daily_spend,
    f.fy25_avg_daily_spend,
    f.fy26_avg_daily_spend,
    f.fy26_ytd_avg_daily_spend,
    f.fy26_forecasted_avg_daily_spend,
    d.daily_cost
FROM daily_costs d
JOIN fiscal_year_averages f
ON d.environment_type = f.environment_type AND d.cto = f.cto
ORDER BY d.date, d.environment_type, d.cto;
```

## Adapting to Different Fiscal Years

If your fiscal year is different:

1. Modify the date ranges in the SQL query above
2. Update the date calculations in `create_html_report.py` where fiscal years are used:
   - Look for patterns like `date BETWEEN '2025-02-01' AND '2026-01-31'`
   - Update with your fiscal year date ranges

## Adapting to Different Schema

If your source data has a different schema:

1. Create a view in BigQuery that transforms your data to match the required schema
2. Point the configuration to your view
3. Alternatively, modify the queries in `create_html_report.py` to work with your schema

## Testing Your Integration

1. Test your BigQuery connection:
```bash
python -c "from google.cloud import bigquery; print(bigquery.Client().query('SELECT 1').result())"
```

2. Test a simple query against your cost data:
```bash
python -c "from google.cloud import bigquery; client = bigquery.Client(); print(client.query('SELECT COUNT(*) FROM `your-project-id.your-dataset.your-cost-table`').result())"
```

3. Run with a limited dataset first:
```bash
python create_html_report.py --output test_report.html
```

## Converting Your Own Data Format

If you need to transform from a different format:

1. Create a Jupyter notebook or Python script to read your source data
2. Transform it to match the required schema
3. Upload to BigQuery using `pandas-gbq` or the BigQuery client
4. Or, create a view in BigQuery that transforms existing data

## Using Multiple Data Sources

To combine multiple data sources:

1. Create a unified view in BigQuery that combines all sources with UNION ALL
2. Ensure the unified view matches the required schema
3. Point the configuration to the unified view

## API and Programmatic Access

You can generate the dashboard programmatically:

```python
from common.finops_config import load_config
from create_html_report import generate_html_report
from google.cloud import bigquery

config = load_config("config.yaml")
client = bigquery.Client(project=config.bigquery_project_id)

generate_html_report(
    client=client,
    project_id=config.bigquery_project_id,
    dataset=config.bigquery_dataset,
    cost_table=config.bigquery_table,
    avg_table=config.avg_table,
    template_path="templates/dashboard_template.html",
    output_path="reports/custom_dashboard.html"
)
```