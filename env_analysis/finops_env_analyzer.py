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
    analyze_env_by_grouping
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
        "--parent-group",
        help="Override parent_grouping in config (e.g. VP, PILLAR, ORG)"
    )
    parser.add_argument(
        "--parent-value",
        help="Override parent_grouping_value in config"
    )
    parser.add_argument(
        "--nonprod-threshold",
        default=20,
        type=float,
        help="Threshold percentage for highlighting high non-production costs (default: 20)"
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
    """Main entry point for the Environment Analyzer."""
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
        period_type = config.period_type
        period_value = config.period_value
        year = config.year
        
        print(f"Analyzing environment data for {period_type}: {period_value}, {year}")
        
        # Filter data for current period
        period_df = get_period_data(
            df, 
            period_type,
            period_value, 
            year, 
            config.parent_grouping, 
            config.parent_grouping_value
        )
        
        if period_df.empty:
            print(f"No data found for the specified period and filters.")
            return 1
        
        # Get environment distribution
        print("Analyzing environment distribution (Prod vs Non-Prod)...")
        env_distribution = get_env_distribution(period_df)
        
        # Analyze by organization (application in new schema)
        print("Analyzing environment distribution by Organization...")
        by_org = analyze_env_by_grouping(
            period_df, 
            'ORG', 
            config.top_n, 
            args.nonprod_threshold
        )
        
        # Analyze by VP
        print("Analyzing environment distribution by VP...")
        by_vp = analyze_env_by_grouping(
            period_df, 
            'VP', 
            config.top_n, 
            args.nonprod_threshold
        )
        
        # Analyze by pillar
        print("Analyzing environment distribution by Pillar...")
        by_pillar = analyze_env_by_grouping(
            period_df, 
            'PILLAR', 
            config.top_n, 
            args.nonprod_threshold
        )
        
        # Analyze by application (or child grouping)
        print(f"Analyzing environment distribution by {config.child_grouping}...")
        by_app = analyze_env_by_grouping(
            period_df, 
            config.child_grouping, 
            config.top_n, 
            args.nonprod_threshold
        )
        
        # Additional analysis for new schema hierarchy
        by_cto = None
        by_subpillar = None
        by_product = None
        
        # Check if we have the new schema columns
        if 'cto' in period_df.columns:
            print("Analyzing environment distribution by CTO...")
            by_cto = analyze_env_by_grouping(
                period_df, 
                'cto', 
                config.top_n, 
                args.nonprod_threshold
            )
        
        if 'tr_subpillar_name' in period_df.columns:
            print("Analyzing environment distribution by Subpillar...")
            by_subpillar = analyze_env_by_grouping(
                period_df, 
                'tr_subpillar_name', 
                config.top_n, 
                args.nonprod_threshold
            )
        
        if 'tr_product' in period_df.columns:
            print("Analyzing environment distribution by Product...")
            by_product = analyze_env_by_grouping(
                period_df, 
                'tr_product', 
                config.top_n, 
                args.nonprod_threshold
            )
        
        # Combine all analyses
        env_analysis = {
            'overall': env_distribution,
            'by_org': by_org,
            'by_vp': by_vp,
            'by_pillar': by_pillar,
            'high_nonprod_groups': by_app['high_nonprod_groups'],
            'nonprod_threshold': args.nonprod_threshold
        }
        
        # Add new schema analyses if available
        if by_cto:
            env_analysis['by_cto'] = by_cto
        if by_subpillar:
            env_analysis['by_subpillar'] = by_subpillar
        if by_product:
            env_analysis['by_product'] = by_product
        
        # Generate HTML report
        if config.generate_html:
            print("Generating HTML report...")
            output_file = generate_env_report_html(
                config, 
                env_analysis,
                config.child_grouping
            )
            print(f"HTML report generated: {output_file}")
        
        # Print summary to console
        print("\n" + "="*70)
        print(f"Environment Cost Analysis Summary")
        print("="*70)
        print(f"Total Cost: ${env_distribution['total_cost']:,.2f}")
        print(f"Production: ${env_distribution['prod_cost']:,.2f} ({env_distribution['prod_percentage']:.2f}%)")
        print(f"Non-Production: ${env_distribution['nonprod_cost']:,.2f} ({env_distribution['nonprod_percentage']:.2f}%)")
        print(f"Applications with high non-prod costs (>={args.nonprod_threshold}%): {len(by_app['high_nonprod_groups'])}")
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