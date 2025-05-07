"""
FinOps Dashboard - Command line interface for generating reports and visualizations.
"""
import os
import argparse
from datetime import datetime
import yaml
from pathlib import Path
import pandas as pd
from google.cloud import bigquery

from common.finops_config import load_config
from analysis.report_generator import generate_report

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='FinOps Dashboard CLI')
    
    # Main command
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate report command
    report_parser = subparsers.add_parser('report', help='Generate cost analysis report')
    report_parser.add_argument('--type', choices=['html', 'txt'], default='html',
                      help='Report output type (default: html)')
    report_parser.add_argument('--comparison', choices=['day', 'week', 'month', 'year'], 
                      default='day', help='Comparison type (default: day)')
    report_parser.add_argument('--trend-days', type=int, default=30,
                      help='Number of days to include in trend (default: 30)')
    report_parser.add_argument('--forecast-days', type=int, default=30,
                      help='Number of days to forecast (default: 30)')
    report_parser.add_argument('--top-teams', type=int, default=5,
                      help='Number of top teams to include (default: 5)')
    report_parser.add_argument('--output-dir', default='output',
                      help='Directory to store the report (default: output)')
    
    # Configure command
    config_parser = subparsers.add_parser('config', help='Configure dashboard settings')
    config_parser.add_argument('--show', action='store_true',
                      help='Show current configuration')
    config_parser.add_argument('--edit', action='store_true',
                      help='Edit configuration file')
    
    return parser.parse_args()

def main():
    """Main entry point for the dashboard."""
    args = parse_arguments()
    
    if not args.command:
        print("Error: No command specified. Use --help for available commands.")
        return
    
    # Load configuration
    config = load_config()
    
    if args.command == 'config':
        if args.show:
            print("Current Configuration:")
            print("=" * 40)
            print(yaml.dump(vars(config), default_flow_style=False))
        elif args.edit:
            # Open the config file in the default editor
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
            os.system(f"open {config_path}")
        else:
            print("Error: Please specify --show or --edit")
    
    elif args.command == 'report':
        # Check if BigQuery is configured
        if not config.use_bigquery:
            print("Error: BigQuery is not enabled in the configuration.")
            return
        
        # Extract BigQuery configuration
        project_id = config.bigquery_project_id
        dataset = config.bigquery_dataset
        table = config.bigquery_table
        
        if not all([project_id, dataset, table]):
            print("Error: Missing BigQuery configuration. Check config.yaml.")
            return
        
        # Get credentials path from config or environment
        credentials_path = config.bigquery_credentials
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        try:
            # Initialize BigQuery client
            client = bigquery.Client(project=project_id)
            
            # Generate the report
            print(f"Generating {args.type} report with {args.comparison} comparison...")
            report_path = generate_report(
                client=client,
                project_id=project_id,
                dataset=dataset,
                table=table,
                output_dir=args.output_dir,
                report_type=args.type,
                comparison_type=args.comparison,
                trend_days=args.trend_days,
                forecast_days=args.forecast_days,
                top_teams=args.top_teams
            )
            
            print(f"Report generated successfully: {report_path}")
            
            # Open the report if it's HTML
            if args.type == 'html':
                os.system(f"open {report_path}")
            
        except Exception as e:
            print(f"Error generating report: {str(e)}")
    
if __name__ == '__main__':
    main()