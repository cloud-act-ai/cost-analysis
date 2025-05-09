#!/bin/bash
# Script to run BigQuery view creation for FinOps360 cost analysis

# Get configuration from config.yaml
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG_PATH="${BASE_DIR}/config.yaml"
PROJECT_ID=$(grep -A3 "project_id:" "${CONFIG_PATH}" | grep "project_id:" | awk '{print $2}' | tr -d '"')
DATASET=$(grep -A3 "dataset:" "${CONFIG_PATH}" | grep "dataset:" | awk '{print $2}' | tr -d '"')
COST_TABLE=$(grep -A3 "table:" "${CONFIG_PATH}" | grep "table:" | awk '{print $2}' | tr -d '"')
AVG_TABLE=$(grep -A3 "avg_table:" "${CONFIG_PATH}" | grep "avg_table:" | awk '{print $2}' | tr -d '"')
SQL_FILE="app/data/create_avg_daily_view.sql"
TEMP_SQL=$(mktemp)

# Print configuration
echo "Running BigQuery view creation with the following configuration:"
echo "  Project: $PROJECT_ID"
echo "  Dataset: $DATASET"
echo "  Cost Table: $COST_TABLE"
echo "  Avg Table: $AVG_TABLE"
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

# Replace variables in SQL file
echo "Preparing SQL script with configuration values..."
cat "$SQL_FILE" | sed \
  -e "s/{project_id}/$PROJECT_ID/g" \
  -e "s/{dataset}/$DATASET/g" \
  -e "s/{cost_table}/$COST_TABLE/g" \
  -e "s/{avg_table}/$AVG_TABLE/g" \
  > "$TEMP_SQL"

# Run the SQL script to create views
echo "Running SQL script to create views..."
bq query --use_legacy_sql=false < "$TEMP_SQL"

if [ $? -ne 0 ]; then
  echo "Error: Failed to create views!"
  rm "$TEMP_SQL"
  exit 1
fi

# Clean up
rm "$TEMP_SQL"

echo "Views created successfully."