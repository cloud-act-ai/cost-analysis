#!/usr/bin/env python3

"""
Simple Environment Analysis Pipeline
Runs BigQuery SQL scripts to analyze environment costs and generate summary.
"""

import os
import sys
import argparse
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

def generate_simple_report(project_id):
    """Generate a simple text report of environment analysis."""
    # Query the summary data
    summary_query = """
    SELECT
      environment_category,
      total_cost,
      environment_summary,
      recommendation
    FROM 
      `finops360-dev-2025.test.env_analysis_consolidated`
    """
    
    client = bigquery.Client(project=project_id)
    rows = client.query(summary_query).result()
    
    # Format timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    month = datetime.now().strftime('%b')
    fy = "FY" + str(datetime.now().year)
    filename = f"env_analysis_report_month_{month}_{fy}_{timestamp}.txt"
    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "output", filename)
    
    # Generate report
    with open(report_path, 'w') as f:
        f.write("======================================\n")
        f.write("  ENVIRONMENT ANALYSIS SUMMARY\n")
        f.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("======================================\n\n")
        
        for row in rows:
            f.write(f"## {row.environment_category} Environment\n")
            f.write(f"Total Cost: ${row.total_cost:,.2f}\n")
            f.write(f"\nSummary: {row.environment_summary}\n")
            f.write(f"\nRecommendation: {row.recommendation}\n")
            f.write("\n" + "-" * 50 + "\n\n")
    
    return report_path

def main():
    parser = argparse.ArgumentParser(description='Run environment analysis pipeline')
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--skip-models', action='store_true', help='Skip model creation step (use existing models)')
    
    args = parser.parse_args()
    
    # Base directory for SQL files
    base_dir = os.path.dirname(os.path.realpath(__file__))
    sql_dir = os.path.join(base_dir, 'sql')
    
    # Define the pipeline steps
    pipeline_steps = [
        {
            'name': 'environment_models',
            'file': os.path.join(sql_dir, 'environment_analysis_models.sql'),
            'description': 'Creating environment analysis models',
            'skip_if': args.skip_models
        },
        {
            'name': 'anomaly_detection',
            'file': os.path.join(sql_dir, 'environment_anomaly_detection.sql'),
            'description': 'Detecting environment cost anomalies'
        },
        {
            'name': 'environment_forecast',
            'file': os.path.join(sql_dir, 'environment_forecast.sql'),
            'description': 'Generating environment cost forecasts'
        },
        {
            'name': 'cost_analysis',
            'file': os.path.join(sql_dir, 'environment_cost_analysis.sql'),
            'description': 'Analyzing environment cost patterns'
        },
        {
            'name': 'genai_summary',
            'file': os.path.join(sql_dir, 'simple_environment_insights.sql'),
            'description': 'Generating environment analysis summary'
        }
    ]
    
    # Run each pipeline step
    for step in pipeline_steps:
        if step.get('skip_if', False):
            print(f"Skipping {step['description']}...")
            continue
            
        print(f"Step: {step['description']}...")
        try:
            sql = read_sql_file(step['file'])
            
            # Split SQL by semicolons to handle multiple statements
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            for i, statement in enumerate(statements):
                if statement.strip():
                    print(f"  Running SQL statement {i+1}/{len(statements)}...")
                    results = run_query(statement, args.project)
                    print(f"  SQL statement {i+1} completed successfully.")
            
            print(f"Step {step['name']} completed successfully.")
        except Exception as e:
            print(f"Error in step {step['name']}: {e}")
            sys.exit(1)
    
    # Generate the simple report
    try:
        print("Generating simple text report...")
        report_path = generate_simple_report(args.project)
        print(f"Report generated successfully: {report_path}")
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)
    
    print("Environment analysis pipeline completed successfully!")

if __name__ == "__main__":
    main()