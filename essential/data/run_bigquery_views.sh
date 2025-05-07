#!/bin/bash
# Script to create BigQuery views for average daily costs with enhanced calculations

# Configuration
PROJECT_ID="finops360-dev-2025"
DATASET="test"
COST_TABLE="cost_analysis_new"
AVG_TABLE="avg_daily_cost_table"
SQL_FILE="data/create_avg_daily_view.sql"

# Print configuration
echo "Creating BigQuery views with the following configuration:"
echo "  Project: $PROJECT_ID"
echo "  Dataset: $DATASET"
echo "  Cost Table: $COST_TABLE"
echo "  Average Daily Table: $AVG_TABLE"
echo "  SQL File: $SQL_FILE"

# Check if necessary files exist
if [ ! -f "$SQL_FILE" ]; then
  echo "Error: SQL file $SQL_FILE not found!"
  exit 1
fi

# Check if bq command is available
if ! command -v bq &> /dev/null; then
  echo "Error: Google Cloud CLI's bq command not found!"
  echo "Please install the Google Cloud CLI from https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Check if the user is logged in
if ! bq ls &> /dev/null; then
  echo "Error: You need to be logged in to Google Cloud to use bq."
  echo "Please run 'gcloud auth login' first."
  exit 1
fi

# Execute the SQL file to create views
echo "Creating views..."
bq query --project_id="$PROJECT_ID" --use_legacy_sql=false < "$SQL_FILE"

if [ $? -ne 0 ]; then
  echo "Error: Failed to create views!"
  exit 1
fi

# List the views in the dataset
echo "Listing views in $PROJECT_ID:$DATASET:"
bq ls --project_id="$PROJECT_ID" "$DATASET" | grep VIEW

echo "Views created successfully!"

# Run a sample query to test the view
echo "Running sample query on the avg_daily_cost_table view..."
bq query --project_id="$PROJECT_ID" --use_legacy_sql=false "
SELECT 
  environment_type,
  COUNT(*) as record_count,
  AVG(fy24_avg_daily_spend) as avg_fy24_spend,
  AVG(fy25_avg_daily_spend) as avg_fy25_spend,
  AVG(fy26_ytd_avg_daily_spend) as avg_fy26_ytd_spend,
  AVG(fy26_forecasted_avg_daily_spend) as avg_fy26_forecast,
  AVG(daily_cost) as avg_daily_cost
FROM \`$PROJECT_ID.$DATASET.$AVG_TABLE\`
GROUP BY environment_type
ORDER BY environment_type
"

echo "Running sample query on the environment_breakdown view..."
bq query --project_id="$PROJECT_ID" --use_legacy_sql=false "
SELECT 
  environment_type,
  AVG(yoy_percent_change) as avg_yoy_change,
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNT(DISTINCT date) as date_count
FROM \`$PROJECT_ID.$DATASET.environment_breakdown\`
GROUP BY environment_type
ORDER BY environment_type
"

echo "Running sample query on the cto_cost_trends view..."
bq query --project_id="$PROJECT_ID" --use_legacy_sql=false "
SELECT 
  cto,
  environment_type,
  avg_fy25_spend,
  avg_fy26_ytd_spend,
  fy25_to_fy26_growth
FROM \`$PROJECT_ID.$DATASET.cto_cost_trends\`
ORDER BY avg_fy26_ytd_spend DESC
LIMIT 5
"

echo "
Successfully created and verified the following views:
1. avg_daily_cost_table - Main view with average cost calculations
2. environment_breakdown - Environment level cost breakdown
3. cto_cost_trends - CTO level cost trends and growth rates
4. monthly_forecasts - Monthly forecast and comparison data
5. year_over_year_comparison - YoY cost comparison with change categories
6. detailed_cost_categories - Detailed cost breakdown by cloud, product, etc.

You can now use these views to create dashboards in your BI tool of choice.
"