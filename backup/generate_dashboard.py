#!/usr/bin/env python3
"""
Script to generate dashboards from BigQuery data.
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from common.finops_bigquery_dashboard import generate_dashboard
from common.finops_config import load_config

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate FinOps dashboards from BigQuery data")
    
    parser.add_argument('--environment', type=str, choices=['PROD', 'NON-PROD', 'ALL'],
                       default='ALL', help="Environment to filter by (default: ALL)")
    parser.add_argument('--cto', type=str, help="CTO to filter by")
    parser.add_argument('--days', type=int, default=30,
                       help="Number of days to include in the dashboard (default: 30)")
    parser.add_argument('--output-dir', type=str, default='reports',
                       help="Output directory for dashboard charts (default: reports)")
    parser.add_argument('--config', type=str, default='config.yaml',
                       help="Path to config file (default: config.yaml)")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Validate BigQuery configuration
        if not config.use_bigquery:
            logger.error("BigQuery is not enabled in the configuration.")
            sys.exit(1)
        
        # Set up BigQuery client
        credentials_path = config.get('bigquery_credentials')
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
        client = bigquery.Client(project=config.bigquery_project_id)
        
        # Set up date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=args.days)
        
        # Process environment filter
        env_filter = None
        if args.environment != 'ALL':
            env_filter = args.environment
            
        # Generate dashboard
        logger.info(f"Generating dashboard for the past {args.days} days...")
        logger.info(f"Environment filter: {env_filter or 'ALL'}")
        logger.info(f"CTO filter: {args.cto or 'ALL'}")
        
        charts = generate_dashboard(
            client=client,
            project_id=config.bigquery_project_id,
            dataset=config.bigquery_dataset,
            environment_filter=env_filter,
            cto_filter=args.cto,
            date_range=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
            output_dir=args.output_dir
        )
        
        # Print results
        if 'error' in charts:
            logger.error(f"Error generating dashboard: {charts['error']}")
            sys.exit(1)
            
        logger.info(f"Generated {len(charts)} charts:")
        for chart_name, chart_path in charts.items():
            logger.info(f"  - {chart_name}: {chart_path}")
            
        logger.info(f"Dashboard generation complete. Charts saved to {args.output_dir}.")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()