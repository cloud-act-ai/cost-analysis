"""
Main entry point for FinOps360 cost analysis dashboard.
"""
import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional

import pandas as pd
from google.cloud import bigquery

from app.utils.config import load_config
from app.dashboard import generate_html_report

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate FinOps HTML dashboard")
    
    parser.add_argument('--output', type=str, default='reports/finops_dashboard.html',
                       help="Output HTML file path (default: reports/finops_dashboard.html)")
    parser.add_argument('--config', type=str, default='config.yaml',
                       help="Path to config file (default: config.yaml)")
    parser.add_argument('--template', type=str, default='app/templates/dashboard_template.html',
                       help="Path to HTML template (default: app/templates/dashboard_template.html)")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Load configuration
        config = load_config(args.config)
        
        # Validate BigQuery configuration
        if not config.get('use_bigquery'):
            logger.warning("BigQuery is not enabled in the configuration. Creating sample dashboard with placeholder data.")
            # Continue with sample data generation instead of exiting
        
        # Check if BigQuery is enabled
        use_bigquery = config.get('use_bigquery', False)
        
        if use_bigquery:
            # Set up BigQuery client
            credentials_path = config.get('bigquery_credentials')
            if credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                
            try:
                client = bigquery.Client(project=config.bigquery_project_id)
            except Exception as e:
                logger.warning(f"Failed to create BigQuery client: {e}")
                use_bigquery = False
                client = None
        else:
            # Create a dummy client for the function signature
            client = None
        
        # Generate HTML report
        report_path = generate_html_report(
            client=client,
            project_id=config.get('bigquery_project_id', 'sample-project'),
            dataset=config.get('bigquery_dataset', 'sample-dataset'),
            cost_table=config.get('bigquery_table', 'sample-table'),
            avg_table=config.get('avg_table', 'avg_daily_cost_table'),
            template_path=args.template,
            output_path=args.output,
            use_bigquery=use_bigquery
        )
        
        # Open the report if in a desktop environment
        if os.name == 'posix':  # macOS or Linux
            os.system(f"open {report_path}")
        elif os.name == 'nt':   # Windows
            os.system(f"start {report_path}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()