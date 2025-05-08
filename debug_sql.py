#!/usr/bin/env python3
"""
Debug script to test SQL queries and date calculations.
"""
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

from google.cloud import bigquery

from app.utils.config import load_config
from app.utils.bigquery import load_sql_query, run_query
from app.data_access import (
    get_ytd_costs,
    get_fy26_costs,
    get_fy25_costs,
    get_recent_comparisons,
    get_product_costs,
    get_daily_trend_data
)

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("debug_sql")

def verify_bigquery_connection(project_id):
    """Verify BigQuery connection and project access."""
    try:
        client = bigquery.Client(project=project_id)
        logger.info(f"Successfully connected to BigQuery project: {project_id}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to BigQuery: {e}")
        return None

def list_tables(client, project_id, dataset):
    """List tables in the dataset."""
    try:
        tables = list(client.list_tables(f"{project_id}.{dataset}"))
        logger.info(f"Found {len(tables)} tables in {project_id}.{dataset}:")
        for table in tables:
            logger.info(f"- {table.table_id}")
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")

def check_table_data(client, project_id, dataset, table, date_column="date"):
    """Check data in the table."""
    try:
        # Check if table exists
        table_ref = client.dataset(dataset).table(table)
        try:
            table_obj = client.get_table(table_ref)
            logger.info(f"Table exists: {project_id}.{dataset}.{table}")
            
            # Get schema
            logger.info("Schema:")
            for field in table_obj.schema:
                logger.info(f"- {field.name}: {field.field_type}")
                
            # Get row count
            query = f"""
            SELECT COUNT(*) as count
            FROM `{project_id}.{dataset}.{table}`
            """
            count_df = client.query(query).to_dataframe()
            logger.info(f"Table has {count_df['count'][0]} rows")
            
            # Check date range
            if date_column in [field.name for field in table_obj.schema]:
                query = f"""
                SELECT MIN({date_column}) as min_date, MAX({date_column}) as max_date
                FROM `{project_id}.{dataset}.{table}`
                """
                date_df = client.query(query).to_dataframe()
                logger.info(f"Date range: {date_df['min_date'][0]} to {date_df['max_date'][0]}")
            
            # Sample data
            query = f"""
            SELECT *
            FROM `{project_id}.{dataset}.{table}`
            LIMIT 5
            """
            sample_df = client.query(query).to_dataframe()
            logger.info("Sample data:")
            logger.info(sample_df)
            
        except Exception as e:
            logger.error(f"Failed to get table: {e}")
    except Exception as e:
        logger.error(f"Failed to check table data: {e}")

def test_day_comparison(client, project_id, dataset, table, day_current, day_previous):
    """Test day comparison query."""
    logger.info("\n==== Testing Day Comparison ====")
    logger.info(f"Current day: {day_current}")
    logger.info(f"Previous day: {day_previous}")
    
    # Load query template
    query_template = load_sql_query("day_comparison")
    logger.info(f"Query template loaded, length: {len(query_template)}")
    
    # Format query with parameters
    query = query_template.format(
        project_id=project_id,
        dataset=dataset,
        table=table,
        day_current=day_current,
        day_previous=day_previous
    )
    
    logger.info(f"Formatted query: \n{query}")
    
    # Run query
    try:
        df = run_query(client, query)
        logger.info(f"Query returned {len(df)} rows")
        if not df.empty:
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"Results: \n{df}")
        return df
    except Exception as e:
        logger.error(f"Error running day comparison query: {e}")
        return None

def test_week_comparison(client, project_id, dataset, table, 
                        week_current_start, week_current_end, 
                        week_previous_start, week_previous_end):
    """Test week comparison query."""
    logger.info("\n==== Testing Week Comparison ====")
    logger.info(f"Current week: {week_current_start} to {week_current_end}")
    logger.info(f"Previous week: {week_previous_start} to {week_previous_end}")
    
    # Load query template
    query_template = load_sql_query("week_comparison")
    logger.info(f"Query template loaded, length: {len(query_template)}")
    
    # Format query with parameters
    query = query_template.format(
        project_id=project_id,
        dataset=dataset,
        table=table,
        this_week_start=week_current_start,
        this_week_end=week_current_end,
        prev_week_start=week_previous_start,
        prev_week_end=week_previous_end
    )
    
    logger.info(f"Formatted query: \n{query}")
    
    # Run query
    try:
        df = run_query(client, query)
        logger.info(f"Query returned {len(df)} rows")
        if not df.empty:
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"Results: \n{df}")
        return df
    except Exception as e:
        logger.error(f"Error running week comparison query: {e}")
        return None

def test_month_comparison(client, project_id, dataset, table, month_current, month_previous):
    """Test month comparison query."""
    logger.info("\n==== Testing Month Comparison ====")
    logger.info(f"Current month: {month_current}")
    logger.info(f"Previous month: {month_previous}")
    
    # Parse month strings to get start and end dates
    this_month_year, this_month_month = map(int, month_current.split('-'))
    prev_month_year, prev_month_month = map(int, month_previous.split('-'))
    
    # First day of each month
    this_month_start = f"{month_current}-01"
    prev_month_start = f"{month_previous}-01"
    
    # Calculate last day of each month
    if this_month_month == 12:
        next_month_year = this_month_year + 1
        next_month_month = 1
    else:
        next_month_year = this_month_year
        next_month_month = this_month_month + 1
        
    if prev_month_month == 12:
        next_prev_month_year = prev_month_year + 1
        next_prev_month_month = 1
    else:
        next_prev_month_year = prev_month_year
        next_prev_month_month = prev_month_month + 1
    
    # Calculate end dates as first day of next month minus one day
    this_month_date = datetime(this_month_year, this_month_month, 1)
    next_month_date = datetime(next_month_year, next_month_month, 1)
    this_month_end = (next_month_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    prev_month_date = datetime(prev_month_year, prev_month_month, 1)
    next_prev_month_date = datetime(next_prev_month_year, next_prev_month_month, 1)
    prev_month_end = (next_prev_month_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    logger.info(f"Calculated date ranges:")
    logger.info(f"Current month: {this_month_start} to {this_month_end}")
    logger.info(f"Previous month: {prev_month_start} to {prev_month_end}")
    
    # Load query template
    query_template = load_sql_query("month_comparison")
    logger.info(f"Query template loaded, length: {len(query_template)}")
    
    # Format query with parameters
    query = query_template.format(
        project_id=project_id,
        dataset=dataset,
        table=table,
        this_month_start=this_month_start,
        this_month_end=this_month_end,
        prev_month_start=prev_month_start,
        prev_month_end=prev_month_end
    )
    
    logger.info(f"Formatted query: \n{query}")
    
    # Run query
    try:
        df = run_query(client, query)
        logger.info(f"Query returned {len(df)} rows")
        if not df.empty:
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"Results: \n{df}")
        return df
    except Exception as e:
        logger.error(f"Error running month comparison query: {e}")
        return None

def test_daily_trend_data(client, project_id, dataset, avg_table):
    """Test daily trend data query."""
    logger.info("\n==== Testing Daily Trend Data ====")
    
    # Calculate date range
    end_date = datetime.now().date() - timedelta(days=3)  # Latest available data
    start_date = end_date - timedelta(days=90)
    
    logger.info(f"Date range: {start_date} to {end_date}")
    
    # Load query template
    query_template = load_sql_query("daily_trend_data")
    logger.info(f"Query template loaded, length: {len(query_template)}")
    
    # Format query with parameters
    query = query_template.format(
        project_id=project_id,
        dataset=dataset,
        avg_table=avg_table,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    logger.info(f"Formatted query: \n{query}")
    
    # Run query
    try:
        df = run_query(client, query)
        logger.info(f"Query returned {len(df)} rows")
        if not df.empty:
            logger.info(f"Columns: {df.columns.tolist()}")
            logger.info(f"Sample rows: \n{df.head()}")
        return df
    except Exception as e:
        logger.error(f"Error running daily trend data query: {e}")
        return None

def test_all_together(client, project_id, dataset, cost_table, avg_table, 
                     day_current_date, day_previous_date,
                     week_current_start, week_current_end,
                     week_previous_start, week_previous_end,
                     month_current, month_previous):
    """Test all functions together."""
    logger.info("\n==== Testing All Together ====")
    
    try:
        # Get YTD costs
        ytd_costs = get_ytd_costs(client, project_id, dataset, cost_table)
        logger.info(f"YTD costs returned {len(ytd_costs)} rows")
        
        # Get FY26 costs
        fy26_costs = get_fy26_costs(client, project_id, dataset, cost_table)
        logger.info(f"FY26 costs returned {len(fy26_costs)} rows")
        
        # Get FY25 costs
        fy25_costs = get_fy25_costs(client, project_id, dataset, cost_table)
        logger.info(f"FY25 costs returned {len(fy25_costs)} rows")
        
        # Get recent comparisons
        day_comparison, week_comparison, month_comparison, date_info = get_recent_comparisons(
            client, project_id, dataset, cost_table, 
            day_current_date=day_current_date, 
            day_previous_date=day_previous_date,
            week_current_start=week_current_start, 
            week_current_end=week_current_end,
            week_previous_start=week_previous_start, 
            week_previous_end=week_previous_end,
            month_current=month_current, 
            month_previous=month_previous
        )
        
        logger.info(f"Day comparison returned {len(day_comparison)} rows")
        logger.info(f"Week comparison returned {len(week_comparison)} rows")
        logger.info(f"Month comparison returned {len(month_comparison)} rows")
        
        # Get product costs
        product_costs = get_product_costs(client, project_id, dataset, cost_table)
        logger.info(f"Product costs returned {len(product_costs)} rows")
        
        # Get daily trend data
        daily_trend_data = get_daily_trend_data(client, project_id, dataset, avg_table)
        logger.info(f"Daily trend data returned {len(daily_trend_data)} rows")
        
        logger.info("All data access functions succeeded!")
        
    except Exception as e:
        logger.error(f"Error testing all together: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Debug SQL queries for FinOps360 dashboard")
    parser.add_argument('--config', type=str, default='config.yaml',
                        help="Path to config file (default: config.yaml)")
    parser.add_argument('--test', type=str, choices=['connection', 'tables', 'day', 'week', 'month', 'daily', 'all'], 
                        default='all', help="Test to run")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Get BigQuery settings
    project_id = config.get('bigquery', {}).get('project_id')
    dataset = config.get('bigquery', {}).get('dataset')
    cost_table = config.get('bigquery', {}).get('table')
    avg_table = config.get('bigquery', {}).get('avg_table')
    
    # Get date settings from config
    data_config = config.get('data', {})
    day_current_date = data_config.get('day_current_date', '2025-05-03')
    day_previous_date = data_config.get('day_previous_date', '2025-05-02')
    week_current_start = data_config.get('week_current_start', '2025-04-27')
    week_current_end = data_config.get('week_current_end', '2025-05-03')
    week_previous_start = data_config.get('week_previous_start', '2025-04-20')
    week_previous_end = data_config.get('week_previous_end', '2025-04-26')
    month_current = data_config.get('month_current', '2025-04')
    month_previous = data_config.get('month_previous', '2025-03')
    
    logger.info(f"Using BigQuery project: {project_id}")
    logger.info(f"Dataset: {dataset}")
    logger.info(f"Cost table: {cost_table}")
    logger.info(f"Avg table: {avg_table}")
    
    # Verify BigQuery connection
    client = verify_bigquery_connection(project_id)
    if client is None:
        logger.error("Failed to connect to BigQuery. Exiting.")
        sys.exit(1)
    
    # Run requested test
    if args.test == 'connection':
        # Already verified above
        pass
    elif args.test == 'tables':
        list_tables(client, project_id, dataset)
        check_table_data(client, project_id, dataset, cost_table)
        check_table_data(client, project_id, dataset, avg_table)
    elif args.test == 'day':
        test_day_comparison(client, project_id, dataset, cost_table, day_current_date, day_previous_date)
    elif args.test == 'week':
        test_week_comparison(client, project_id, dataset, cost_table, 
                            week_current_start, week_current_end, 
                            week_previous_start, week_previous_end)
    elif args.test == 'month':
        test_month_comparison(client, project_id, dataset, cost_table, month_current, month_previous)
    elif args.test == 'daily':
        test_daily_trend_data(client, project_id, dataset, avg_table)
    elif args.test == 'all':
        # Run all tests
        list_tables(client, project_id, dataset)
        check_table_data(client, project_id, dataset, cost_table)
        check_table_data(client, project_id, dataset, avg_table)
        test_day_comparison(client, project_id, dataset, cost_table, day_current_date, day_previous_date)
        test_week_comparison(client, project_id, dataset, cost_table, 
                            week_current_start, week_current_end, 
                            week_previous_start, week_previous_end)
        test_month_comparison(client, project_id, dataset, cost_table, month_current, month_previous)
        test_daily_trend_data(client, project_id, dataset, avg_table)
        test_all_together(client, project_id, dataset, cost_table, avg_table,
                         day_current_date, day_previous_date,
                         week_current_start, week_current_end,
                         week_previous_start, week_previous_end,
                         month_current, month_previous)
    
    logger.info("Debug script completed.")

if __name__ == "__main__":
    main()