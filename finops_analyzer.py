#!/usr/bin/env python3
"""
FinOps360 Environment Analysis Tool
----------------------------------
Main entry point for environment cost analysis.
Provides command-line interface to run environment analysis.
"""

import os
import sys
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="FinOps360 Environment Analysis Tool")
    
    # Environment analysis parameters
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--parent-group",
        help="Parent grouping (e.g. VP, PILLAR, ORG)"
    )
    parser.add_argument(
        "--parent-value",
        help="Parent grouping value"
    )
    parser.add_argument(
        "--nonprod-threshold",
        default=20,
        type=float,
        help="Threshold percentage for high non-production costs (default: 20)"
    )
    parser.add_argument(
        "--period",
        help="Period type (month, quarter, week, year)"
    )
    parser.add_argument(
        "--period-value",
        help="Period value"
    )
    parser.add_argument(
        "--year",
        help="Year for analysis"
    )
    
    # BigQuery parameters
    parser.add_argument(
        "--use-bigquery", 
        action="store_true",
        help="Use BigQuery as the data source"
    )
    parser.add_argument(
        "--project-id",
        help="Google Cloud project ID for BigQuery"
    )
    parser.add_argument(
        "--dataset",
        help="BigQuery dataset name"
    )
    parser.add_argument(
        "--table",
        help="BigQuery table name"
    )
    parser.add_argument(
        "--credentials",
        help="Path to Google Cloud service account credentials JSON file"
    )
    parser.add_argument(
        "--disable-bqdf",
        action="store_true",
        help="Disable BigQuery DataFrames and use pandas_gbq instead (less efficient for large datasets)"
    )
    parser.add_argument(
        "--select-columns",
        help="Comma-separated list of columns to fetch from BigQuery (reduces data transfer). Example: 'cost,month,environment,fy'"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the FinOps Environment Analyzer."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Run environment analysis
        from env_analysis.finops_env_analyzer import main as env_main
        env_args = [
            "--config", args.config,
            "--nonprod-threshold", str(args.nonprod_threshold)
        ]
        
        # Add optional arguments if provided
        if args.parent_group:
            env_args.extend(["--parent-group", args.parent_group])
        if args.parent_value:
            env_args.extend(["--parent-value", args.parent_value])
        if args.period:
            env_args.extend(["--period", args.period])
        if args.period_value:
            env_args.extend(["--period-value", args.period_value])
        if args.year:
            env_args.extend(["--year", args.year])
        
        # Check for BigQuery command-line arguments
        if args.use_bigquery:
            env_args.append("--use-bigquery")
            
            # Only require these if they're not configured in the config file
            # We need to check the config file for these values
            config_file = args.config
            
            try:
                # Load just the config file to check if BigQuery settings are there
                with open(config_file, 'r') as f:
                    import yaml
                    config_data = yaml.safe_load(f)
                    
                has_bq_config = 'bigquery' in config_data and config_data['bigquery'].get('use_bigquery', False)
                has_project_id = args.project_id or (has_bq_config and config_data['bigquery'].get('project_id'))
                has_dataset = args.dataset or (has_bq_config and config_data['bigquery'].get('dataset'))
                has_table = args.table or (has_bq_config and config_data['bigquery'].get('table'))
                
                if not (has_project_id and has_dataset and has_table):
                    raise ValueError("When using BigQuery, project-id, dataset, and table are required (either via command line or config.yaml)")
            except (FileNotFoundError, yaml.YAMLError):
                # If can't read config, fall back to requiring command line args
                if not args.project_id or not args.dataset or not args.table:
                    raise ValueError("When using BigQuery, project-id, dataset, and table are required")
            
            # Pass command-line arguments if provided
            if args.project_id:
                env_args.extend(["--project-id", args.project_id])
            if args.dataset:
                env_args.extend(["--dataset", args.dataset])
            if args.table:
                env_args.extend(["--table", args.table])
            if args.credentials:
                env_args.extend(["--credentials", args.credentials])
            
            # Pass BigQuery DataFrames flag if specified
            if args.disable_bqdf:
                env_args.append("--disable-bqdf")
            
            # Pass column selection if specified
            if args.select_columns:
                env_args.extend(["--select-columns", args.select_columns])
        
        # Update sys.argv for the environment analyzer
        sys.argv = [sys.argv[0]] + env_args
        return env_main()
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())