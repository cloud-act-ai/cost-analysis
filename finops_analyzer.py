#!/usr/bin/env python3
"""
FinOps360 Cost Analysis Tool
----------------------------
Analyzes cloud cost data and generates reports based on config.yaml settings.
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Import local modules
from finops_config import load_config, get_output_filename
from finops_data import (
    load_data, 
    get_month_data, 
    get_previous_month, 
    analyze_cost_changes
)
from finops_html import generate_html_report


def main():
    """Main entry point for the FinOps Analyzer."""
    try:
        # Load configuration
        config = load_config()
        
        # Create output directory if it doesn't exist
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Load and preprocess data
        print(f"Loading data from {config.file_path}...")
        df = load_data(config.file_path)
        
        # Get current month data
        current_month = config.month
        current_year = config.year
        print(f"Analyzing data for {current_month} {current_year}...")
        
        current_df = get_month_data(
            df, 
            current_month, 
            current_year, 
            config.parent_grouping, 
            config.parent_grouping_value
        )
        
        # Get previous month data
        previous_month, previous_year = get_previous_month(current_month, current_year)
        print(f"Comparing with previous month: {previous_month} {previous_year}")
        
        previous_df = get_month_data(
            df, 
            previous_month, 
            previous_year, 
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
                current_month, 
                previous_month, 
                current_year, 
                previous_year
            )
            print(f"HTML report generated: {output_file}")
        
        # Print summary to console
        print("\n" + "="*50)
        print(f"FinOps Summary for {config.parent_grouping}: {config.parent_grouping_value}")
        print("="*50)
        print(f"Previous Month Spend ({previous_month} {previous_year}): ${analysis_results['total_previous']:,.2f}")
        print(f"Current Month Spend ({current_month} {current_year}): ${analysis_results['total_current']:,.2f}")
        print(f"Efficiencies (Cost Reduction): ${analysis_results['efficiencies']:,.2f}")
        print(f"Investments (Cost Increase): +${analysis_results['investments']:,.2f}")
        print(f"Net Change: ${analysis_results['net_change']:,.2f} ({analysis_results['percent_change']:.2f}%)")
        print("="*50)
        
        print("\nAnalysis completed successfully!")
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())