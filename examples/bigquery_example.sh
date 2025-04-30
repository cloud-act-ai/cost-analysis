#!/bin/bash
# Example showing how to use the analyzer with BigQuery

# Set the BigQuery parameters
PROJECT_ID="finops360-dev-2025"
DATASET="test"
TABLE="cost_analysis_test"
CREDENTIALS="path/to/your/service-account-key.json"  # Optional, if using default credentials

# Run the analyzer with BigQuery as the data source
python ../finops_analyzer.py \
  --config ../config.yaml \
  --use-bigquery \
  --project-id "$PROJECT_ID" \
  --dataset "$DATASET" \
  --table "$TABLE" \
  --nonprod-threshold 5.0

# Note: If you need to use service account credentials, add:
# --credentials "$CREDENTIALS"

# Run with period filtering
# python ../finops_analyzer.py \
#   --config ../config.yaml \
#   --use-bigquery \
#   --project-id "$PROJECT_ID" \
#   --dataset "$DATASET" \
#   --table "$TABLE" \
#   --period "month" \
#   --period-value "Mar" \
#   --year "FY2024" \
#   --nonprod-threshold 5.0

# Run with parent-group filtering
# python ../finops_analyzer.py \
#   --config ../config.yaml \
#   --use-bigquery \
#   --project-id "$PROJECT_ID" \
#   --dataset "$DATASET" \
#   --table "$TABLE" \
#   --parent-group "cto" \
#   --parent-value "Michael Chen" \
#   --nonprod-threshold 5.0