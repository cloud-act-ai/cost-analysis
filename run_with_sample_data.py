#!/usr/bin/env python3
"""
Run the FinOps analysis with sample data (without BigQuery).
This script simulates a BigQuery environment using local CSV data.
"""
import os
import sys
import argparse
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a mock BigQuery client class to handle local data
class MockBigQueryClient:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        logger.info(f"Loaded {len(self.data)} rows from {data_path}")
        
        # Convert date components to date
        if 'day_of_month' not in self.data.columns:
            # Add day_of_month column (set to 1 if missing)
            self.data['day_of_month'] = 1
            
        # Create date column from components
        self.data['date'] = pd.to_datetime(
            self.data['year'].astype(str) + '-' + 
            self.data['month'].astype(str) + '-' + 
            self.data['day_of_month'].astype(str)
        )
    
    def query(self, query):
        """Mock query execution using pandas."""
        # Extract key parts from the query
        conditions = []
        group_by = []
        
        # This is a very simple SQL parser - only handles basic conditions
        if 'WHERE' in query:
            where_clause = query.split('WHERE')[1].split('GROUP BY')[0] if 'GROUP BY' in query else query.split('WHERE')[1]
            # Split by AND and extract conditions
            for condition in where_clause.split('AND'):
                condition = condition.strip()
                
                # Handle year/month comparisons
                if 'year =' in condition:
                    year = condition.split('=')[1].strip()
                    conditions.append(f"self.data['year'] == {year}")
                elif 'year >' in condition:
                    year = condition.split('>')[1].strip()
                    conditions.append(f"self.data['year'] > {year}")
                elif 'month =' in condition:
                    month = condition.split('=')[1].strip()
                    conditions.append(f"self.data['month'] == {month}")
                elif 'month >=' in condition:
                    month = condition.split('>=')[1].strip()
                    conditions.append(f"self.data['month'] >= {month}")
                elif 'month <=' in condition:
                    month = condition.split('<=')[1].strip()
                    conditions.append(f"self.data['month'] <= {month}")
                elif 'environment IN' in condition:
                    env_list = condition.split('IN')[1].strip('() ').replace("'", "").split(',')
                    env_list = [e.strip() for e in env_list]
                    env_list_str = str(env_list)
                    conditions.append(f"self.data['environment'].str.lower().isin([e.lower() for e in {env_list_str}])")
                elif 'environment NOT IN' in condition:
                    env_list = condition.split('IN')[1].strip('() ').replace("'", "").split(',')
                    env_list = [e.strip() for e in env_list]
                    env_list_str = str(env_list)
                    conditions.append(f"~self.data['environment'].str.lower().isin([e.lower() for e in {env_list_str}])")
        
        # Handle GROUP BY
        if 'GROUP BY' in query:
            group_clause = query.split('GROUP BY')[1].split('ORDER BY')[0] if 'ORDER BY' in query else query.split('GROUP BY')[1]
            group_by = [g.strip() for g in group_clause.split(',')]
        
        # Apply filters
        filtered_data = self.data
        if conditions:
            combined_condition = ' & '.join(conditions)
            try:
                filtered_data = self.data[eval(combined_condition)]
            except Exception as e:
                logger.error(f"Error applying filter: {e}")
                logger.error(f"Condition was: {combined_condition}")
                return MockQueryResult(pd.DataFrame())
        
        # Extract relevant columns and perform aggregations if needed
        if 'SELECT' in query:
            select_clause = query.split('SELECT')[1].split('FROM')[0]
            selected_fields = []
            
            # Very simple field extractor - handles basic cases only
            if 'SUM(cost)' in select_clause:
                if group_by:
                    result = filtered_data.groupby(group_by).agg({'cost': 'sum'}).reset_index()
                    result.rename(columns={'cost': 'total_cost'}, inplace=True)
                else:
                    total = filtered_data['cost'].sum()
                    result = pd.DataFrame({'total_cost': [total]})
            elif 'AVG(cost)' in select_clause:
                if group_by:
                    result = filtered_data.groupby(group_by).agg({'cost': 'mean'}).reset_index()
                    result.rename(columns={'cost': 'avg_cost'}, inplace=True)
                else:
                    avg = filtered_data['cost'].mean()
                    result = pd.DataFrame({'avg_cost': [avg]})
            else:
                # Default case - just return filtered data with basic grouping
                if group_by:
                    result = filtered_data.groupby(group_by).agg({
                        'cost': ['sum', 'mean']
                    }).reset_index()
                    result.columns = group_by + ['total_cost', 'avg_cost']
                else:
                    result = filtered_data
        else:
            result = filtered_data
        
        # Add environment label formatting for better display
        if 'environment' in result.columns:
            result['environment'] = result['environment'].apply(
                lambda x: 'Production' if x == 'p' else 'Non-Production' if x == 'np' else x
            )
            
        return MockQueryResult(result)

class MockQueryResult:
    def __init__(self, df):
        self.df = df
    
    def result(self):
        return self
    
    def to_dataframe(self, create_bqstorage_client=True):
        return self.df

def run_sample_report(
    data_path: str,
    output_dir: str = "output",
    report_type: str = "html",
    comparison_type: str = "month",
    trend_days: int = 30,
    forecast_days: int = 30,
    top_teams: int = 5
):
    """
    Run a report generation using sample data instead of BigQuery.
    
    Args:
        data_path: Path to CSV data file
        output_dir: Output directory for reports
        report_type: Report type (html or txt)
        comparison_type: Comparison type (day, week, month, year)
        trend_days: Days to include in trend analysis
        forecast_days: Days to forecast
        top_teams: Number of top teams to include
    """
    # Import here to avoid circular imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from analysis.report_generator import generate_report
    
    # Create mock BigQuery client
    client = MockBigQueryClient(data_path)
    
    # Fake BigQuery parameters
    project_id = "sample-project"
    dataset = "sample_dataset"
    table = "sample_table"
    
    # Generate report
    print(f"Generating {report_type} report with {comparison_type} comparison...")
    try:
        report_path = generate_report(
            client=client,
            project_id=project_id,
            dataset=dataset,
            table=table,
            output_dir=output_dir,
            report_type=report_type,
            comparison_type=comparison_type,
            trend_days=trend_days,
            forecast_days=forecast_days,
            top_teams=top_teams
        )
        
        print(f"Report generated successfully: {report_path}")
        
        # Open the report if it's HTML
        if report_type == "html":
            os.system(f"open {report_path}")
            
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate FinOps report with sample data")
    
    parser.add_argument('--data', type=str, default="finops_data.csv",
                      help="Path to CSV data file (default: finops_data.csv)")
    parser.add_argument('--type', type=str, choices=['html', 'txt'], default='html',
                      help="Report output type (default: html)")
    parser.add_argument('--comparison', type=str, choices=['day', 'week', 'month', 'year'], 
                      default='month', help="Comparison type (default: month)")
    parser.add_argument('--trend-days', type=int, default=30,
                      help="Number of days to include in trend (default: 30)")
    parser.add_argument('--forecast-days', type=int, default=30,
                      help="Number of days to forecast (default: 30)")
    parser.add_argument('--top-teams', type=int, default=5,
                      help="Number of top teams to include (default: 5)")
    parser.add_argument('--output-dir', type=str, default='output',
                      help="Directory to store report (default: output)")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    run_sample_report(
        data_path=args.data,
        output_dir=args.output_dir,
        report_type=args.type,
        comparison_type=args.comparison,
        trend_days=args.trend_days,
        forecast_days=args.forecast_days,
        top_teams=args.top_teams
    )