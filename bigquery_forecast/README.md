# BigQuery Time Series Forecast & GenAI Analysis

This module provides advanced cost analysis using BigQuery's ML capabilities for time series forecasting and GenAI insights.

## Features

- **Time Series Forecasting**: Uses BigQuery ML.FORECAST to predict future costs
- **Anomaly Detection**: Identifies cost anomalies using statistical methods
- **Trend Analysis**: Shows month-over-month and year-over-year cost trends
- **Resource Utilization**: Analyzes resource usage patterns to identify optimization opportunities
- **GenAI Insights**: Uses BigQuery's ML.GENERATE_TEXT to provide natural language analysis

## Structure

- `/sql`: Contains all SQL queries for analysis
  - `create_forecast_model.sql`: Creates the time series forecast model
  - `time_series_forecast.sql`: Generates forecasts using the model
  - `cost_anomaly_detection.sql`: Detects cost anomalies
  - `trend_analysis.sql`: Analyzes cost trends over time
  - `resource_utilization.sql`: Identifies underutilized resources
  - `create_llm_model.sql`: Creates connection to LLM for GenAI analysis
  - `genai_cost_analysis.sql`: Generates natural language insights

- `/config`: Configuration files
  - `table_schema.json`: Schema definition for cost data table

## Usage

Run the analysis using the Python script:

```bash
python3 run_forecast.py --project your-gcp-project-id --query all
```

Or run specific analyses:

```bash
python3 run_forecast.py --project your-gcp-project-id --query forecast
python3 run_forecast.py --project your-gcp-project-id --query anomaly
python3 run_forecast.py --project your-gcp-project-id --query genai
```

## Prerequisites

- BigQuery dataset with cost analysis data in table `finops360-dev-2025.test.cost_analysis_test`
- Google Cloud project with BigQuery ML and Vertex AI API enabled
- Appropriate permissions to create models and run queries

## Table Schema

The expected schema for the cost analysis table includes:
- `usage_date`: Date when cost was incurred
- `service`: Cloud service (e.g., Compute Engine)
- `environment`: Environment name (prod, dev, etc.)
- `project_id`: Google Cloud project identifier
- `cost`: Cost amount in USD
- `region`: Cloud region (optional)
- `resource_type`: Type of resource (optional)
- `tags`: Resource labels (optional)