#!/usr/bin/env python3

"""
Environment Analysis Pipeline
Runs BigQuery SQL scripts to analyze environment costs, detect anomalies,
forecast future costs, and generate executive summary.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
import json
from google.cloud import bigquery
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import base64
from io import BytesIO

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

def query_to_dataframe(query, project_id):
    """Run a query and return results as a pandas DataFrame."""
    client = bigquery.Client(project=project_id)
    return client.query(query).to_dataframe()

def generate_environment_charts(project_id):
    """Generate charts for environment analysis."""
    charts = {}
    
    # Environment cost distribution
    env_cost_query = """
    SELECT
      environment_category,
      SUM(total_cost) as total_cost
    FROM
      `finops360-dev-2025.test.env_cost_summary`
    GROUP BY
      environment_category
    ORDER BY
      total_cost DESC
    """
    env_cost_df = query_to_dataframe(env_cost_query, project_id)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x='environment_category', y='total_cost', data=env_cost_df)
    plt.title('Total Cost by Environment Category')
    plt.ylabel('Total Cost ($)')
    plt.xlabel('Environment Category')
    for i, p in enumerate(ax.patches):
        ax.annotate(f'${p.get_height():,.0f}', 
                   (p.get_x() + p.get_width() / 2., p.get_height()),
                   ha = 'center', va = 'bottom', xytext = (0, 10), 
                   textcoords = 'offset points')
    
    # Save to BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    charts['env_cost_distribution'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Environment anomalies
    anomaly_query = """
    SELECT
      environment_category,
      COUNT(*) as anomaly_count,
      COUNT(CASE WHEN severity = 'Critical' THEN 1 END) as critical_count,
      COUNT(CASE WHEN severity = 'High' THEN 1 END) as high_count,
      COUNT(CASE WHEN severity = 'Medium' THEN 1 END) as medium_count
    FROM
      `finops360-dev-2025.test.env_anomalies_consolidated`
    GROUP BY
      environment_category
    """
    anomaly_df = query_to_dataframe(anomaly_query, project_id)
    
    plt.figure(figsize=(12, 6))
    anomaly_df_melted = pd.melt(anomaly_df, 
                               id_vars=['environment_category'],
                               value_vars=['critical_count', 'high_count', 'medium_count'],
                               var_name='severity', value_name='count')
    anomaly_df_melted['severity'] = anomaly_df_melted['severity'].str.replace('_count', '')
    ax = sns.barplot(x='environment_category', y='count', hue='severity', data=anomaly_df_melted)
    plt.title('Anomalies by Environment Category and Severity')
    plt.ylabel('Count')
    plt.xlabel('Environment Category')
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    charts['anomalies'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Environment efficiency
    efficiency_query = """
    SELECT
      environment_category,
      CASE WHEN environment_category = 'Production' THEN 1.0 ELSE SAFE_DIVIDE(total_cost, 
        (SELECT SUM(total_cost) FROM `finops360-dev-2025.test.env_cost_summary` 
         WHERE environment_category = 'Production')) END as cost_ratio
    FROM
      (SELECT environment_category, SUM(total_cost) as total_cost
       FROM `finops360-dev-2025.test.env_cost_summary`
       GROUP BY environment_category)
    """
    efficiency_df = query_to_dataframe(efficiency_query, project_id)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x='environment_category', y='cost_ratio', data=efficiency_df)
    plt.title('Environment Cost Ratio (Relative to Production)')
    plt.ylabel('Cost Ratio')
    plt.xlabel('Environment Category')
    for i, p in enumerate(ax.patches):
        ax.annotate(f'{p.get_height():.2f}x', 
                   (p.get_x() + p.get_width() / 2., p.get_height()),
                   ha = 'center', va = 'bottom', xytext = (0, 10), 
                   textcoords = 'offset points')
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    charts['efficiency'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Forecast growth by environment
    forecast_query = """
    SELECT
      environment_category,
      AVG(projected_growth_pct) as avg_growth_pct
    FROM
      `finops360-dev-2025.test.env_forecasts_consolidated`
    WHERE
      DATE(forecast_date) = DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY
      environment_category
    """
    forecast_df = query_to_dataframe(forecast_query, project_id)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x='environment_category', y='avg_growth_pct', data=forecast_df)
    plt.title('Projected 30-Day Cost Growth by Environment')
    plt.ylabel('Average Projected Growth (%)')
    plt.xlabel('Environment Category')
    for i, p in enumerate(ax.patches):
        ax.annotate(f'{p.get_height():,.1f}%', 
                   (p.get_x() + p.get_width() / 2., p.get_height()),
                   ha = 'center', va = 'bottom' if p.get_height() > 0 else 'top', 
                   xytext = (0, 10 if p.get_height() > 0 else -10), 
                   textcoords = 'offset points')
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    charts['forecast'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return charts

def generate_html_report(project_id):
    """Generate HTML report with all analysis results."""
    # Query the summary data
    summary_query = "SELECT * FROM `finops360-dev-2025.test.env_analysis_consolidated`"
    summary_df = query_to_dataframe(summary_query, project_id)
    
    # Get top anomalies
    anomalies_query = """
    SELECT
      environment_category,
      date,
      tr_product_pillar_team,
      service_name,
      cost,
      baseline_cost,
      percent_change,
      severity
    FROM
      `finops360-dev-2025.test.env_anomalies_consolidated`
    ORDER BY
      CASE WHEN severity = 'Critical' THEN 1
           WHEN severity = 'High' THEN 2
           ELSE 3 END,
      percent_change DESC
    LIMIT 10
    """
    anomalies_df = query_to_dataframe(anomalies_query, project_id)
    
    # Get top forecasted items
    forecast_query = """
    SELECT
      environment_category,
      DATE(forecast_date) as forecast_date,
      tr_product_pillar_team,
      service_name,
      forecasted_cost,
      current_avg_cost,
      projected_growth_pct
    FROM
      `finops360-dev-2025.test.env_forecasts_consolidated`
    WHERE
      DATE(forecast_date) = DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY)
    ORDER BY
      ABS(projected_growth_pct) DESC
    LIMIT 10
    """
    forecast_df = query_to_dataframe(forecast_query, project_id)
    
    # Get environment efficiency data
    efficiency_query = """
    SELECT
      tr_product_pillar_team,
      service_name,
      prod_cost,
      dev_cost,
      test_cost,
      non_prod_to_prod_ratio,
      efficiency_rating
    FROM
      `finops360-dev-2025.test.env_efficiency_metrics`
    ORDER BY
      non_prod_to_prod_ratio DESC
    LIMIT 10
    """
    efficiency_df = query_to_dataframe(efficiency_query, project_id)
    
    # Generate charts
    charts = generate_environment_charts(project_id)
    
    # Create HTML report using Jinja2 template
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Environment Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2, h3 { color: #333366; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
            tr:hover {background-color: #f5f5f5;}
            .summary-box { 
                border: 1px solid #ddd; 
                padding: 15px; 
                margin-bottom: 20px; 
                border-radius: 5px;
                background-color: #f9f9f9;
            }
            .chart-container {
                display: inline-block;
                width: 48%;
                margin: 10px;
                vertical-align: top;
            }
            .chart {
                width: 100%;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .critical { background-color: #ffdddd; }
            .high { background-color: #ffffcc; }
            .warning { background-color: #fff6e6; }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .date-info {
                text-align: right;
                font-size: 0.9em;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Environment Analysis Report</h1>
            <div class="date-info">
                <p>Analysis Date: {{ today }}</p>
                <p>Report Generated: {{ now }}</p>
            </div>
        </div>
        
        <h2>Executive Summary</h2>
        {% for _, row in summary.iterrows() %}
        <div class="summary-box">
            <h3>{{ row.environment_category }} Environment</h3>
            <p><strong>Total Cost:</strong> ${{ '{:,.2f}'.format(row.total_cost) }}</p>
            <p><strong>Summary:</strong> {{ row.environment_summary }}</p>
            <p><strong>Recommendation:</strong> {{ row.recommendation }}</p>
        </div>
        {% endfor %}
        
        <h2>Environment Cost Visualizations</h2>
        <div class="chart-container">
            <h3>Environment Cost Distribution</h3>
            <img src="data:image/png;base64,{{ charts.env_cost_distribution }}" class="chart">
        </div>
        <div class="chart-container">
            <h3>Environment Cost Efficiency</h3>
            <img src="data:image/png;base64,{{ charts.efficiency }}" class="chart">
        </div>
        <div class="chart-container">
            <h3>Anomalies by Environment</h3>
            <img src="data:image/png;base64,{{ charts.anomalies }}" class="chart">
        </div>
        <div class="chart-container">
            <h3>Projected 30-Day Growth</h3>
            <img src="data:image/png;base64,{{ charts.forecast }}" class="chart">
        </div>
        
        <h2>Top Cost Anomalies</h2>
        <table>
            <tr>
                <th>Environment</th>
                <th>Date</th>
                <th>Team</th>
                <th>Service</th>
                <th>Cost</th>
                <th>Baseline</th>
                <th>% Change</th>
                <th>Severity</th>
            </tr>
            {% for _, row in anomalies.iterrows() %}
            <tr class="{{ row.severity.lower() if row.severity.lower() in ['critical', 'high'] else '' }}">
                <td>{{ row.environment_category }}</td>
                <td>{{ row.date.strftime('%Y-%m-%d') }}</td>
                <td>{{ row.tr_product_pillar_team }}</td>
                <td>{{ row.service_name }}</td>
                <td>${{ '{:,.2f}'.format(row.cost) }}</td>
                <td>${{ '{:,.2f}'.format(row.baseline_cost) }}</td>
                <td>{{ '{:+.1f}%'.format(row.percent_change) }}</td>
                <td>{{ row.severity }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Top Forecasted Cost Changes (30-Day Projection)</h2>
        <table>
            <tr>
                <th>Environment</th>
                <th>Forecast Date</th>
                <th>Team</th>
                <th>Service</th>
                <th>Current Cost</th>
                <th>Forecasted Cost</th>
                <th>Growth %</th>
            </tr>
            {% for _, row in forecast.iterrows() %}
            <tr class="{{ 'warning' if abs(row.projected_growth_pct) > 15 else '' }}">
                <td>{{ row.environment_category }}</td>
                <td>{{ row.forecast_date.strftime('%Y-%m-%d') }}</td>
                <td>{{ row.tr_product_pillar_team }}</td>
                <td>{{ row.service_name }}</td>
                <td>${{ '{:,.2f}'.format(row.current_avg_cost) }}</td>
                <td>${{ '{:,.2f}'.format(row.forecasted_cost) }}</td>
                <td>{{ '{:+.1f}%'.format(row.projected_growth_pct) }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Top Environment Efficiency Concerns</h2>
        <table>
            <tr>
                <th>Team</th>
                <th>Service</th>
                <th>Prod Cost</th>
                <th>Dev Cost</th>
                <th>Test Cost</th>
                <th>Non-Prod/Prod Ratio</th>
                <th>Efficiency Rating</th>
            </tr>
            {% for _, row in efficiency.iterrows() %}
            <tr class="{{ 'warning' if 'Poor' in row.efficiency_rating else '' }}">
                <td>{{ row.tr_product_pillar_team }}</td>
                <td>{{ row.tr_product }}</td>
                <td>{{ row.service_name }}</td>
                <td>${{ '{:,.2f}'.format(row.prod_cost) }}</td>
                <td>${{ '{:,.2f}'.format(row.dev_cost) }}</td>
                <td>${{ '{:,.2f}'.format(row.test_cost) }}</td>
                <td>{{ '{:.2f}'.format(row.non_prod_to_prod_ratio) }}</td>
                <td>{{ row.efficiency_rating }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <footer>
            <p>Generated with FinOps360 Environment Analysis Pipeline</p>
        </footer>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(
        summary=summary_df,
        anomalies=anomalies_df,
        forecast=forecast_df,
        efficiency=efficiency_df,
        charts=charts,
        today=datetime.now().strftime('%Y-%m-%d'),
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # Save the report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    month = datetime.now().strftime('%b')
    fy = "FY" + str(datetime.now().year)
    filename = f"env_analysis_report_month_{month}_{fy}_{timestamp}.html"
    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "output", filename)
    
    with open(report_path, 'w') as f:
        f.write(html_content)
    
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
            'file': os.path.join(sql_dir, 'environment_genai_summary.sql'),
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
    
    # Generate the HTML report
    try:
        print("Generating HTML report...")
        report_path = generate_html_report(args.project)
        print(f"Report generated successfully: {report_path}")
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)
    
    print("Environment analysis pipeline completed successfully!")

if __name__ == "__main__":
    main()