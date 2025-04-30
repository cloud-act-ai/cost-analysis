# FinOps360 Environment Analysis Tool

A tool for analyzing cloud environment costs (Production vs Non-Production) and generating reports.

## Overview

The Environment Analysis Tool helps organizations understand and optimize their cloud spending across different environments. It provides insights into:

- Overall Production vs Non-Production cost distribution
- Environment breakdown by Organization, VP, and Pillar
- Applications with high non-production costs

## Requirements

- Python 3.8+
- Required packages:
  - pandas>=2.0.0
  - jinja2>=3.0.0
  - pyyaml>=6.0.0
  - google-cloud-bigquery>=3.0.0 (for BigQuery support)
  - pandas-gbq>=0.19.0 (for BigQuery support)
  - pyarrow>=12.0.0 (for BigQuery support)

Install requirements:

```bash
pip install -r requirements.txt
```

## Usage

You can run the tool directly:

```bash
python finops_analyzer.py --config config.yaml [OPTIONS]
```

### Command-line Options

#### General Options
- `--config`: Path to configuration file (default: config.yaml)
- `--parent-group`: Override parent_grouping in config (e.g. VP, PILLAR, ORG)
- `--parent-value`: Override parent_grouping_value in config
- `--nonprod-threshold`: Threshold percentage for highlighting high non-production costs (default: 20)
- `--period`: Override period_type in config (month, quarter, week, year)
- `--period-value`: Override period_value in config
- `--year`: Override year in config

#### BigQuery Options
- `--use-bigquery`: Use BigQuery as the data source instead of a CSV file
- `--project-id`: Google Cloud project ID for BigQuery
- `--dataset`: BigQuery dataset name
- `--table`: BigQuery table name
- `--credentials`: Path to Google Cloud service account credentials JSON file (optional)

### Configuration File

The `config.yaml` file contains settings for the analysis:

```yaml
# Data sources and paths
data:
  file_path: data/finops_data.csv
  output_dir: output

# Analysis settings
analysis:
  # Time period configuration
  period_type: month  # Options: month, quarter, week, year
  period_value: Mar   # Month name, quarter (Q1-Q4), week number, or year
  year: 2024
  
  # Grouping configuration
  parent_grouping: ORG  # Can be any column in dataset: ORG, VP, PILLAR, etc.
  parent_grouping_value: Starling  # Default value for parent grouping
  
  # Child grouping for detailed analysis
  child_grouping: Application_Name
  top_n: 10
  include_applications: true
  
  # Environment analysis settings
  nonprod_threshold: 20  # Percentage threshold for highlighting high non-prod costs
  
  # Display columns (optional)
  display_columns:
    - Application_Name
    - ORG
    - VP
    - PILLAR
    - Cloud
    - Env
    - Cost

# Report settings
report:
  generate_html: true
  export_csv: true
  page_title: Cloud Spend Management Report
  company_name: FinOps
  logo_path: ""
```

## Data Format

### CSV Data Source
The analysis expects a CSV file with at least the following columns:
- `Env` or `environment`: Environment type (Prod, Dev, Stage, Test, QA)
- `Cost` or `cost`: Numeric cost values
- Grouping columns: `ORG`, `VP`, `PILLAR`, `Application_Name`, or equivalent new schema columns
- Time columns: `Month`, `QTR`/`qtr`, `WM_WEEK`/`week`, `FY`/`fy`

Sample data is available in `data/finops_data.csv`.

### BigQuery Data Source
When using BigQuery, the table should have a similar schema:
- `environment`: Environment type (Prod, Dev, Stage, Test, QA)
- `cost`: Numeric cost values
- Grouping columns: `cto`, `vp`, `tr_product_pillar_team`, `tr_subpillar_name`, `tr_product`, `application`
- Time columns: `date`, `Month`, `qtr`, `week`, `fy`

Example BigQuery Schema:
```
field name               mode      type      description
date                    NULLABLE   DATE    
year                    NULLABLE   INTEGER    
cloud                   NULLABLE   STRING    
cto                     NULLABLE   STRING    
vp                      NULLABLE   STRING    
tr_product_pillar_team  NULLABLE   STRING    
tr_subpillar_id         NULLABLE   INTEGER    
tr_subpillar_name       NULLABLE   STRING    
tr_product              NULLABLE   STRING    
tr_product_id           NULLABLE   INTEGER    
owner                   NULLABLE   STRING    
application             NULLABLE   STRING    
service_name            NULLABLE   STRING    
environment             NULLABLE   STRING    
region                  NULLABLE   STRING    
project_id              NULLABLE   STRING    
cost                    NULLABLE   FLOAT    
fy                      NULLABLE   STRING    
qtr                     NULLABLE   INTEGER    
week                    NULLABLE   INTEGER    
Month                   NULLABLE   STRING
```

Example of running with BigQuery:
```bash
python finops_analyzer.py --config config.yaml --use-bigquery \
  --project-id "finops360-dev-2025" --dataset "test" \
  --table "cost_analysis_test" --nonprod-threshold 5.0
```

## Output

The tool generates HTML reports in the output directory specified in the configuration. Reports include:
- Overall environment distribution
- Environment breakdown by type
- Environment distribution by organization, VP, and pillar
- Applications with high non-production costs