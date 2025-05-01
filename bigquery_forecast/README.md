# Environment Analysis for Cloud Cost Management

This package provides advanced cloud cost analysis tools focused on different environments (Production, Development, Test/Stage), using ARIMA+ time series forecasting models and anomaly detection to provide actionable insights.

## Features

- **Environment-specific Analysis**: Compare costs across Production, Development, and Test/Stage environments
- **Time Series Forecasting**: Uses BigQuery ML.FORECAST with ARIMA_PLUS models to predict future costs
- **Anomaly Detection**: Identifies cost anomalies across environments
- **Efficiency Metrics**: Calculates Development-to-Production and Test-to-Production cost ratios
- **Automated Insights**: Generates actionable recommendations for cost optimization

## Directory Structure

```
bigquery_forecast/
├── sql/                           # SQL queries
│   ├── environment_analysis_models.sql     # Environment-specific time series models
│   ├── environment_anomaly_detection.sql   # Cost anomaly detection across environments
│   ├── environment_cost_analysis.sql       # Environment cost patterns and efficiency
│   ├── environment_forecast.sql            # 30-day forecasts by environment
│   └── simple_environment_insights.sql     # Consolidated insights with recommendations
└── analyze_environments_simple.py          # Execution script
```

## Usage

```bash
# Run the complete analysis
python analyze_environments_simple.py --project YOUR_GCP_PROJECT_ID

# Skip model creation (use existing models)
python analyze_environments_simple.py --project YOUR_GCP_PROJECT_ID --skip-models
```

## Analysis Process

1. **Data Organization**: Groups cloud costs by environment categories
2. **Time Series Models**: Creates separate forecasting models for each environment
3. **Anomaly Detection**: Uses statistical methods to identify cost outliers 
4. **Forecasting**: Projects costs 30 days into the future
5. **Insight Generation**: Produces summarized insights and recommendations

## Output

The script generates a text report with environment-specific analysis:
- Total costs by environment
- Optimization potential with estimated savings
- Cost distribution and ratios between environments
- Anomalies and forecasted growth
- Top cost contributors
- Specific recommendations for each environment

Reports are saved to the `../output/` directory with timestamps.

## Prerequisites

- BigQuery dataset containing cost data
- Appropriate permissions for creating models and running queries
- Python 3.6+ with google-cloud-bigquery package installed