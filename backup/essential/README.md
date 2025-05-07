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

## Setup

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

## Data Structure

### Primary Tables

1. **cost_analysis_new**: Raw cost data with the following schema:
   - date: Date of the cost entry
   - cto: CTO/Tech leadership organization
   - cloud: Cloud provider (AWS, Azure, GCP)
   - tr_product_pillar_team: Product pillar team
   - tr_subpillar_name: Sub-pillar name
   - tr_product_id: Product ID
   - tr_product: Product name
   - managed_service: Cloud managed service
   - environment: Environment (PROD, NON-PROD)
   - cost: Daily cost in USD

2. **avg_daily_cost_table**: Average cost data with the following schema:
   - date: Date of the cost entry
   - environment_type: Environment type (PROD, NON-PROD)
   - cto: CTO/Tech leadership organization
   - fy24_avg_daily_spend: FY24 average daily spend
   - fy25_avg_daily_spend: FY25 average daily spend
   - fy26_ytd_avg_daily_spend: FY26 year-to-date average daily spend
   - fy26_forecasted_avg_daily_spend: FY26 forecasted average daily spend
   - fy26_avg_daily_spend: FY26 total average daily spend
   - daily_cost: Current daily cost

## Fiscal Year Definitions

The system uses the following fiscal year date ranges:

- **FY24**: 2023-02-01 to 2024-01-31
- **FY25**: 2024-02-01 to 2025-01-31
- **FY26**: 2025-02-01 to 2026-01-31

## Key Calculations

- **YTD Costs**: Sum of costs from the beginning of the current fiscal year to present
- **Average Daily Spend**: Total cost divided by number of days, providing a normalized metric for comparison
- **NON-PROD Percentage**: Percentage of NON-PROD costs relative to total costs, showing efficiency of development environments
- **Day/Week/Month Comparisons**: Period-over-period comparisons showing cost trends with percentage changes

## Usage

### Generate HTML Dashboard

```bash
python create_html_report.py
```

Options:
- `--output`: Output HTML file path (default: reports/finops_dashboard.html)
- `--config`: Path to config file (default: config.yaml)
- `--template`: Path to HTML template (default: templates/dashboard_template.html)

### Load Data to BigQuery

```bash
bash data/load_to_bigquery.sh
```

### Create BigQuery Views

```bash
bash data/run_bigquery_views.sh
```

### Generate Sample Data

```bash
python data/generate_updated_data.py --no-header
```

### Clean Up Unnecessary Files

```bash
bash cleanup.sh
```

## Directory Structure

- `analysis/`: Core analysis modules for cost calculations and visualizations
- `common/`: Shared utilities and BigQuery integration services
- `data/`: Data files, schemas, and loading scripts
- `templates/`: HTML templates for dashboard reports
- `reports/`: Generated HTML reports
- `output/`: Output files including charts and comparison reports

## BigQuery Views

The system creates the following BigQuery views:

1. **avg_daily_cost_table**: Main view for average daily costs by environment with fiscal year comparisons
2. **environment_breakdown**: Environment-level cost breakdown (PROD vs NON-PROD)
3. **cto_cost_trends**: CTO-level cost trends and growth rates
4. **monthly_forecasts**: Monthly forecast data based on historical growth patterns
5. **year_over_year_comparison**: YoY cost comparison with change categories
6. **detailed_cost_categories**: Detailed cost breakdown by cloud, product, etc.

## Example SQL for avg_daily_cost_table

This view is created using the following logic:

```sql
WITH fiscal_year_averages AS (
    SELECT 
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
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
    FROM cost_analysis_new
    WHERE date BETWEEN '2023-02-01' AND '2026-01-31'
    GROUP BY environment_type, cto
),
daily_costs AS (
    SELECT 
        date,
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        cto,
        ROUND(SUM(cost), 2) AS daily_cost
    FROM cost_analysis_new
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

## License

© 2025 FinOps360