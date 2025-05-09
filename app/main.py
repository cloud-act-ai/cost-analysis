"""
Main entry point for FinOps360 cost analysis dashboard.
"""
import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional, Union

from google.cloud import bigquery

from app.utils.config import load_config
from app.dashboard import generate_html_report

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set specific logging levels
logging.getLogger('app.utils.bigquery').setLevel(logging.DEBUG)
logging.getLogger('app.data_access').setLevel(logging.DEBUG)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate FinOps HTML dashboard")
    
    parser.add_argument('--output', type=str,
                       help="Output HTML file path (overrides config)")
    parser.add_argument('--config', type=str, default='config.yaml',
                       help="Path to config file (default: config.yaml)")
    parser.add_argument('--template', type=str, default='app/templates/dashboard_template.html',
                       help="Path to HTML template (default: app/templates/dashboard_template.html)")
    parser.add_argument('--no-interactive', action='store_true',
                       help="Disable interactive charts")
    parser.add_argument('--debug', action='store_true',
                       help="Enable debug mode with verbose logging")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Configure debug mode if requested
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('app').setLevel(logging.DEBUG)
        logger.info("Debug mode enabled with verbose logging")
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Set the output path from config or command line
        output_path = args.output or os.path.join(config.get('output_dir', 'reports'), 'finops_dashboard.html')
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get project and dataset settings
        project_id = config.get('bigquery_project_id')
        dataset = config.get('bigquery_dataset')
        cost_table = config.get('bigquery_table', 'cost_analysis_new')
        avg_table = config.get('bigquery_avg_table')
        
        # Verify required configurations
        if not project_id or not dataset:
            logger.error("Missing required BigQuery configuration. "
                        "Please set project_id and dataset in config.yaml")
            sys.exit(1)
        
        # Set up BigQuery client
        credentials_path = config.get('bigquery_credentials')
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
        try:
            client = bigquery.Client(project=project_id)
            logger.info(f"Connected to BigQuery project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to create BigQuery client: {e}")
            sys.exit(1)
        
        # Determine if interactive charts should be used
        use_interactive_charts = not args.no_interactive and config.get('interactive_charts', True)
        
        # Log interactive charts status
        if use_interactive_charts:
            logger.info("Interactive charts enabled")
        else:
            logger.info("Interactive charts disabled")
        
        # Generate HTML report
        report_path = generate_html_report(
            client=client,
            project_id=project_id,
            dataset=dataset,
            cost_table=cost_table,
            avg_table=avg_table,
            template_path=args.template,
            output_path=output_path,
            use_interactive_charts=use_interactive_charts
        )
        
        # Open the report if in a desktop environment
        if os.name == 'posix':  # macOS or Linux
            os.system(f"open {report_path}")
        elif os.name == 'nt':   # Windows
            os.system(f"start {report_path}")
            
    except Exception as e:
        import traceback
        logger.error(f"Error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()