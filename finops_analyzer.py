#!/usr/bin/env python3
"""
FinOps360 Cost Analysis Tool
----------------------------
Analyzes cloud cost data and generates reports based on config.yaml settings.
Supports different time period comparisons and flexible grouping options.
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime

# Import local modules
from finops_config import load_config, validate_config_with_data, get_output_filename
from finops_data import (
    load_data, 
    get_period_data, 
    get_previous_period, 
    get_period_display_name,
    analyze_cost_changes
)
from finops_html import generate_html_report


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="FinOps360 Cost Analysis Tool")
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--parent-group",
        help="Override parent_grouping in config (e.g. VP, PILLAR, ORG)"
    )
    parser.add_argument(
        "--parent-value",
        help="Override parent_grouping_value in config"
    )
    parser.add_argument(
        "--child-group",
        default="Application_Name",
        help="Override child_grouping in config"
    )
    parser.add_argument(
        "--period",
        help="Override period_type in config (month, quarter, week, year)"
    )
    parser.add_argument(
        "--period-value",
        help="Override period_value in config"
    )
    parser.add_argument(
        "--year",
        help="Override year in config"
    )
    return parser.parse_args()


def main():
    """Main entry point for the FinOps Analyzer."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Load configuration
        config = load_config(args.config)
        
        # Override config with command line arguments if provided
        if args.parent_group:
            config.parent_grouping = args.parent_group
        if args.parent_value:
            config.parent_grouping_value = args.parent_value
        if args.child_group:
            config.child_grouping = args.child_group
        if args.period:
            config.period_type = args.period
        if args.period_value:
            config.period_value = args.period_value
        if args.year:
            config.year = args.year
        
        # Create output directory if it doesn't exist
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Load and preprocess data
        print(f"Loading data from {config.file_path}...")
        df = load_data(config.file_path)
        
        # Validate configuration with the actual data
        print("Validating configuration...")
        validate_config_with_data(config, df)
        
        # Get current period data
        current_period_type = config.period_type
        current_period_value = config.period_value
        current_year = config.year
        
        current_period_display = get_period_display_name(
            current_period_type, 
            current_period_value, 
            current_year
        )
        
        print(f"Analyzing data for {current_period_display}, grouping by {config.parent_grouping}: {config.parent_grouping_value}...")
        
        current_df = get_period_data(
            df, 
            current_period_type,
            current_period_value, 
            current_year, 
            config.parent_grouping, 
            config.parent_grouping_value
        )
        
        # Get previous period data
        previous_period_value, previous_year = get_previous_period(
            current_period_type,
            current_period_value, 
            current_year
        )
        
        previous_period_display = get_period_display_name(
            current_period_type, 
            previous_period_value, 
            previous_year if previous_year else current_year
        )
        
        print(f"Comparing with previous period: {previous_period_display}")
        
        previous_df = get_period_data(
            df, 
            current_period_type,
            previous_period_value, 
            previous_year if previous_year else current_year, 
            config.parent_grouping, 
            config.parent_grouping_value
        )
        
        # Analyze cost changes
        print("Analyzing cost changes...")
        analysis_results = analyze_cost_changes(
            current_df, 
            previous_df, 
            config.child_grouping, 
            config.top_n
        )
        
        # Generate HTML report if configured
        if config.generate_html:
            print("Generating HTML report...")
            output_file = generate_html_report(
                config, 
                analysis_results, 
                current_period_display, 
                previous_period_display
            )
            print(f"HTML report generated: {output_file}")
        
        # Print summary to console
        print("\n" + "="*70)
        print(f"FinOps360 Summary for {config.parent_grouping}: {config.parent_grouping_value}")
        print("="*70)
        print(f"Previous {current_period_type.capitalize()} ({previous_period_display}): ${analysis_results['total_previous']:,.2f}")
        print(f"Current {current_period_type.capitalize()} ({current_period_display}): ${analysis_results['total_current']:,.2f}")
        print(f"Efficiencies (Cost Reduction): ${analysis_results['efficiencies']:,.2f}")
        print(f"Investments (Cost Increase): +${analysis_results['investments']:,.2f}")
        print(f"Net Change: ${analysis_results['net_change']:,.2f} ({analysis_results['percent_change']:.2f}%)")
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