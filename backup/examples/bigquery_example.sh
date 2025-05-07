#!/bin/bash
# Example showing how to use the analyzer with BigQuery and BigQuery DataFrames
# BigQuery DataFrames provide more efficient handling of large datasets

##########################################
# METHOD 1: Using Command Line Arguments #
##########################################

# Set the BigQuery parameters
PROJECT_ID="finops360-dev-2025"
DATASET="test"
TABLE="cost_analysis_test"
CREDENTIALS="path/to/your/service-account-key.json"  # Optional, if using default credentials

# Run the analyzer with BigQuery as the data source using command line arguments
python ../finops_analyzer.py \
  --config ../config.yaml \
  --use-bigquery \
  --project-id "$PROJECT_ID" \
  --dataset "$DATASET" \
  --table "$TABLE" \
  --nonprod-threshold 5.0 \
  --select-columns "cost,environment,month,fy,date,application_name"

# Note: If you need to use service account credentials, add:
# --credentials "$CREDENTIALS"

# To disable BigQuery DataFrames and use traditional pandas_gbq:
# --disable-bqdf

##################################
# METHOD 2: Using config.yaml    #
##################################

# Alternatively, you can configure BigQuery in config.yaml:
#
# bigquery:
#   project_id: finops360-dev-2025
#   dataset: test
#   table: cost_analysis_test
#   use_bigquery: true  # Set to true to enable BigQuery as data source
#   use_bqdf: true      # Set to false to disable BigQuery DataFrames
#   selected_columns:   # List of columns to fetch (reduces data transfer)
#     - cost
#     - environment 
#     - month
#     - fy
#     - date
#
# And then simply run:
python ../finops_analyzer.py --config ../config.yaml

# Command line arguments will override config.yaml settings
# For example, this would override the project_id:
# python ../finops_analyzer.py --config ../config.yaml --use-bigquery --project-id "other-project-id"

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