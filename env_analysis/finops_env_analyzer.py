#!/usr/bin/env python3
"""
Environment Cost Analysis Tool
-----------------------------
Analyzes cloud environment costs (Production vs Non-Production) and generates reports.
Provides overall environment distribution and analysis by organization, VP, and pillar.
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime

# Import common modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.finops_config import load_config, validate_config_with_data
from common.finops_data import (
    load_data, 
    get_period_data,
    get_env_distribution,
    analyze_env_by_grouping,
    analyze_hierarchical_env,
    get_last_period,
    get_current_fiscal_year
)
from common.finops_html import generate_env_report_html


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Environment Cost Analysis Tool")
    parser.add_argument(
        "--config", 
        default="../config.yaml",
        help="Path to configuration file (default: ../config.yaml)"
    )
    parser.add_argument(
        "--nonprod-threshold",
        type=float,
        help="Threshold percentage for highlighting high non-production costs (default: 20)"
    )
    parser.add_argument(
        "--period",
        help="Period type to analyze (month, quarter, week, year)"
    )
    parser.add_argument(
        "--period-value",
        help="Period value (or 'last' for most recent period)"
    )
    parser.add_argument(
        "--year",
        help="Year for analysis (or 'current' for current year)"
    )
    # BigQuery arguments
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
    return parser.parse_args()


def main():
    """Main entry point for the Environment Analyzer."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Load configuration
        config = load_config(args.config)
        
        # Override config with command line arguments if provided
        if args.period:
            config.period_type = args.period
        if args.period_value:
            config.period_value = args.period_value
        if args.year:
            config.year = args.year
        if args.nonprod_threshold:
            config.nonprod_threshold = args.nonprod_threshold
            
        # Add BigQuery parameters to config
        if args.use_bigquery:
            config.use_bigquery = True
            config.bigquery_project_id = args.project_id
            config.bigquery_dataset = args.dataset
            config.bigquery_table = args.table
            config.bigquery_credentials = args.credentials
        else:
            config.use_bigquery = False
        
        # Create output directory if it doesn't exist
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Load and preprocess data - either from CSV or BigQuery
        if config.use_bigquery:
            print(f"Loading data from BigQuery table {config.bigquery_project_id}.{config.bigquery_dataset}.{config.bigquery_table}...")
            from common.finops_bigquery import load_data_from_bigquery
            df = load_data_from_bigquery(
                config.bigquery_project_id,
                config.bigquery_dataset,
                config.bigquery_table,
                config.bigquery_credentials
            )
        else:
            print(f"Loading data from {config.file_path}...")
            df = load_data(config.file_path)
        
        # Validate configuration with the actual data
        print("Validating configuration...")
        validate_config_with_data(config, df)
        
        # Get current period data
        period_type = config.period_type
        period_value = config.period_value
        year = config.year
        
        # Get actual period values (resolving 'last' and 'current')
        actual_period_value = period_value
        actual_year = year
        
        if period_value == 'last':
            actual_period_value, period_year = get_last_period(df, period_type)
            if period_year:
                actual_year = period_year
                
        if year == 'current':
            actual_year = get_current_fiscal_year(df)
        
        print(f"Analyzing environment data for {period_type}: {actual_period_value}, {actual_year}")
        
        # Filter data for current period
        if config.use_bigquery:
            # If using BigQuery, we can load just the period data
            from common.finops_bigquery import load_period_data_from_bigquery
            period_df = load_period_data_from_bigquery(
                config.bigquery_project_id,
                config.bigquery_dataset,
                config.bigquery_table,
                period_type,
                period_value,  # Use original value as function handles 'last'
                year,          # Use original value as function handles 'current'
                credentials_path=config.bigquery_credentials
            )
        else:
            # Otherwise, use the full dataframe and filter it
            period_df = get_period_data(
                df, 
                period_type,
                period_value,  # Use original value as get_period_data handles 'last'
                year,          # Use original value as get_period_data handles 'current'
                None,
                None
            )
        
        if period_df.empty:
            print(f"No data found for the specified period and filters.")
            return 1
        
        # Get environment distribution
        print("Analyzing environment distribution (Prod vs Non-Prod)...")
        env_distribution = get_env_distribution(period_df)
        
        # Perform hierarchical analysis using the configured hierarchy
        print("Performing hierarchical environment analysis...")
        
        # Use level-specific top_n values if available
        top_n_values = {}
        if config.top_n_by_level:
            for level in config.hierarchy:
                if level in config.top_n_by_level:
                    top_n_values[level] = config.top_n_by_level[level]
                else:
                    top_n_values[level] = config.top_n
        else:
            # Use the same top_n for all levels
            for level in config.hierarchy:
                top_n_values[level] = config.top_n
        
        hierarchical_analysis = analyze_hierarchical_env(
            period_df, 
            config.hierarchy, 
            top_n_values, 
            config.nonprod_threshold
        )
        
        # Combine analyses
        env_analysis = {
            'overall': env_distribution,
            'hierarchical': hierarchical_analysis,
            'period_type': period_type,
            'period_value': actual_period_value,
            'year': actual_year,
            'nonprod_threshold': config.nonprod_threshold,
            'hierarchy': config.hierarchy,
            'display_columns': config.display_columns
        }
        
        # Generate HTML report
        if config.generate_html:
            print("Generating HTML report...")
            output_file = generate_env_report_html(
                config, 
                env_analysis
            )
            print(f"HTML report generated: {output_file}")
        
        # Print summary to console
        print("\n" + "="*70)
        print(f"Environment Cost Analysis Summary")
        print("="*70)
        print(f"Total Cost: ${env_distribution['total_cost']:,.2f}")
        print(f"Production: ${env_distribution['prod_cost']:,.2f} ({env_distribution['prod_percentage']:.2f}%)")
        print(f"Non-Production: ${env_distribution['nonprod_cost']:,.2f} ({env_distribution['nonprod_percentage']:.2f}%)")
        
        # Count high non-prod applications
        application_level = None
        for level in config.hierarchy:
            if level == 'application':
                application_level = level
                break
        
        if application_level and application_level in hierarchical_analysis['hierarchy_levels']:
            high_nonprod_count = len(hierarchical_analysis['hierarchy_levels'][application_level]['high_nonprod_groups'])
            print(f"Applications with high non-prod costs (>={config.nonprod_threshold}%): {high_nonprod_count}")
        
        print("="*70)
        
        print("\nAnalysis completed successfully!")
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())