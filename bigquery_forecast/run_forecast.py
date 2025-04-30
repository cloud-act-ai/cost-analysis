#!/usr/bin/env python3

"""
BigQuery Forecast Runner
This script executes the BigQuery SQL files for time series forecasting and GenAI analysis.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from google.cloud import bigquery

def read_sql_file(file_path):
    """Read SQL from file."""
    with open(file_path, 'r') as f:
        return f.read()

def run_query(query, project_id):
    """Execute a BigQuery query."""
    client = bigquery.Client(project=project_id)
    job = client.query(query)
    results = job.result()
    return results

def main():
    parser = argparse.ArgumentParser(description='Run BigQuery forecasting queries')
    parser.add_argument('--query', choices=['create_model', 'forecast', 'anomaly', 'genai', 'create_llm', 'all'], 
                        default='all', help='Query type to run')
    parser.add_argument('--project', required=True, help='GCP Project ID')
    
    args = parser.parse_args()
    
    # Base directory for SQL files
    base_dir = os.path.dirname(os.path.realpath(__file__))
    sql_dir = os.path.join(base_dir, 'sql')
    
    # Map of query types to file paths
    queries = {
        'create_model': os.path.join(sql_dir, 'create_forecast_model.sql'),
        'forecast': os.path.join(sql_dir, 'time_series_forecast.sql'),
        'anomaly': os.path.join(sql_dir, 'cost_anomaly_detection.sql'),
        'genai': os.path.join(sql_dir, 'genai_cost_analysis.sql'),
        'create_llm': os.path.join(sql_dir, 'create_llm_model.sql')
    }
    
    # Determine which queries to run
    to_run = []
    if args.query == 'all':
        # For 'all', run all queries but skip the LLM model creation since it's not working
        to_run = ['create_model', 'forecast', 'anomaly', 'genai']
    elif args.query == 'genai':
        # GenAI doesn't require LLM model anymore since we're using rule-based insights
        to_run = ['genai']
    elif args.query == 'forecast':
        to_run = ['create_model', 'forecast']
    else:
        to_run = [args.query]
    
    # Run each selected query
    for query_type in to_run:
        print(f"Running {query_type} query...")
        sql = read_sql_file(queries[query_type])
        try:
            results = run_query(sql, args.project)
            print(f"Query {query_type} completed successfully.")
            
            # Print results for queries that return data
            if query_type in ['forecast', 'anomaly', 'genai']:
                for row in results:
                    print(row)
        except Exception as e:
            print(f"Error running {query_type} query: {e}")
            sys.exit(1)
    
    print("All queries completed successfully!")

if __name__ == "__main__":
    main()