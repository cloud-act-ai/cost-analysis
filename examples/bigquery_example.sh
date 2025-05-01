#!/bin/bash
# Example showing how to use the analyzer with BigQuery and BigQuery DataFrames
# BigQuery DataFrames provide more efficient handling of large datasets

# Set the BigQuery parameters
PROJECT_ID="finops360-dev-2025"
DATASET="test"
TABLE="cost_analysis_test"
CREDENTIALS="path/to/your/service-account-key.json"  # Optional, if using default credentials

# Run the analyzer with BigQuery as the data source using BigQuery DataFrames
# BigQuery DataFrames are enabled by default for better performance with large results
python ../finops_analyzer.py \
  --config ../config.yaml \
  --use-bigquery \
  --project-id "$PROJECT_ID" \
  --dataset "$DATASET" \
  --table "$TABLE" \
  --nonprod-threshold 5.0

# Note: If you need to use service account credentials, add:
# --credentials "$CREDENTIALS"

# To disable BigQuery DataFrames and use traditional pandas_gbq:
# --disable-bqdf

# Run with period filtering
# This pushes filtering to BigQuery server for better performance
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
# This also uses BigQuery server-side filtering
# python ../finops_analyzer.py \
#   --config ../config.yaml \
#   --use-bigquery \
#   --project-id "$PROJECT_ID" \
#   --dataset "$DATASET" \
#   --table "$TABLE" \
#   --parent-group "cto" \
#   --parent-value "Michael Chen" \
#   --nonprod-threshold 5.0

# Advanced example with direct usage of filter and aggregation functions
# For programmatic access in Python scripts:
#
# 1. Filtering example:
# ```python
# from common.finops_bigquery import filter_bigquery_data
#
# # Get all data for dev environments with cost > 1000
# filtered_data = filter_bigquery_data(
#    project_id="finops360-dev-2025",
#    dataset="test",
#    table="cost_analysis_test", 
#    filters={
#        "environment": "dev",
#        "Cost": [">", 1000]
#    }
# )
# ```
#
# 2. Aggregation example:
# ```python
# from common.finops_bigquery import aggregate_bigquery_data
# 
# # Get total cost grouped by environment with having clause
# agg_data = aggregate_bigquery_data(
#    project_id="finops360-dev-2025",
#    dataset="test", 
#    table="cost_analysis_test",
#    group_by=["environment", "Month"],
#    agg_functions={"Cost": "SUM"},
#    filters={"fy": "FY2024"},
#    having={"Cost_sum": [">", 10000]},
#    order_by={"Cost_sum": "DESC"}
# )
# ```