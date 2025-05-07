#!/bin/bash
# Script to run BigQuery view creation for FinOps360 cost analysis

# Configuration
PROJECT_ID="finops360-dev-2025"
DATASET="test"
SQL_FILE="app/data/create_avg_daily_view.sql"

# Print configuration
echo "Running BigQuery view creation with the following configuration:"
echo "  Project: $PROJECT_ID"
echo "  Dataset: $DATASET"
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

# Run the SQL script to create views
echo "Running SQL script to create views..."
bq query --use_legacy_sql=false < "$SQL_FILE"

if [ $? -ne 0 ]; then
  echo "Error: Failed to create views!"
  exit 1
fi

echo "Views created successfully."