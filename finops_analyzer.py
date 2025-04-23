#!/usr/bin/env python3
"""
FinOps360 Analysis Tool
-----------------------
Main entry point for all FinOps analysis tools.
Provides command-line interface to run various analysis modules.
"""

import os
import sys
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="FinOps360 Analysis Tool")
    
    # Create subparsers for different analysis types
    subparsers = parser.add_subparsers(dest="analysis_type", help="Type of analysis to run")
    
    # Cloud spend analysis
    cloud_parser = subparsers.add_parser("cloud", help="Cloud spend analysis")
    cloud_parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    cloud_parser.add_argument(
        "--parent-group",
        help="Parent grouping (e.g. VP, PILLAR, ORG)"
    )
    cloud_parser.add_argument(
        "--parent-value",
        help="Parent grouping value"
    )
    cloud_parser.add_argument(
        "--child-group",
        help="Child grouping for detailed analysis"
    )
    cloud_parser.add_argument(
        "--period",
        help="Period type (month, quarter, week, year)"
    )
    cloud_parser.add_argument(
        "--period-value",
        help="Period value"
    )
    cloud_parser.add_argument(
        "--year",
        help="Year for analysis"
    )
    
    # Environment analysis
    env_parser = subparsers.add_parser("environment", help="Environment (Prod vs Non-Prod) analysis")
    env_parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    env_parser.add_argument(
        "--parent-group",
        help="Parent grouping (e.g. VP, PILLAR, ORG)"
    )
    env_parser.add_argument(
        "--parent-value",
        help="Parent grouping value"
    )
    env_parser.add_argument(
        "--nonprod-threshold",
        default=20,
        type=float,
        help="Threshold percentage for high non-production costs (default: 20)"
    )
    env_parser.add_argument(
        "--period",
        help="Period type (month, quarter, week, year)"
    )
    env_parser.add_argument(
        "--period-value",
        help="Period value"
    )
    env_parser.add_argument(
        "--year",
        help="Year for analysis"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the FinOps Analyzer."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        if args.analysis_type == "cloud":
            # Run cloud spend analysis
            from cloud_analysis.finops_cloud_analyzer import main as cloud_main
            cloud_args = [
                "--config", args.config
            ]
            
            # Add optional arguments if provided
            if args.parent_group:
                cloud_args.extend(["--parent-group", args.parent_group])
            if args.parent_value:
                cloud_args.extend(["--parent-value", args.parent_value])
            if args.child_group:
                cloud_args.extend(["--child-group", args.child_group])
            if args.period:
                cloud_args.extend(["--period", args.period])
            if args.period_value:
                cloud_args.extend(["--period-value", args.period_value])
            if args.year:
                cloud_args.extend(["--year", args.year])
            
            # Update sys.argv for the cloud analyzer
            sys.argv = [sys.argv[0]] + cloud_args
            return cloud_main()
            
        elif args.analysis_type == "environment":
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
            
            # Update sys.argv for the environment analyzer
            sys.argv = [sys.argv[0]] + env_args
            return env_main()
            
        else:
            print("Please specify an analysis type (cloud or environment)")
            print("Example: python finops_analyzer.py cloud --config config.yaml")
            print("Example: python finops_analyzer.py environment --config config.yaml")
            return 1
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())