#!/bin/bash
# Script to create BigQuery views for FinOps analysis

# Configuration
PROJECT_ID="finops360-dev-2025"
DATASET="test"
SQL_FILE="data/create_views.sql"

# Print configuration
echo "Creating BigQuery views with the following configuration:"
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