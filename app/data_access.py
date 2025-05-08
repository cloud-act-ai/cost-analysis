"""
Data access functions for FinOps360 cost analysis dashboard.
"""
import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Any, Optional

import pandas as pd
from google.cloud import bigquery

from app.utils.bigquery import run_query, load_sql_query

logger = logging.getLogger(__name__)

def get_ytd_costs(client: bigquery.Client, project_id: str, dataset: str, table: str) -> pd.DataFrame:
    """
    Get year-to-date costs for production and non-production.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        
    Returns:
        DataFrame with YTD costs by environment
    """
    query = load_sql_query("ytd_costs", project_id=project_id, dataset=dataset, table=table)
    return run_query(client, query)

def get_fy26_costs(client: bigquery.Client, project_id: str, dataset: str, table: str) -> pd.DataFrame:
    """
    Get projected FY26 costs for production and non-production.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        
    Returns:
        DataFrame with FY26 costs by environment
    """
    query = load_sql_query("fy26_costs", project_id=project_id, dataset=dataset, table=table)
    return run_query(client, query)

def get_fy25_costs(client: bigquery.Client, project_id: str, dataset: str, table: str) -> pd.DataFrame:
    """
    Get FY25 costs for year-over-year comparison.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        
    Returns:
        DataFrame with FY25 costs by environment
    """
    query = load_sql_query("fy25_costs", project_id=project_id, dataset=dataset, table=table)
    return run_query(client, query)

def get_recent_comparisons(client: bigquery.Client, project_id: str, dataset: str, table: str,
                       day_current_date: str = "2025-05-03", day_previous_date: str = "2025-05-02",
                       week_current_start: str = "2025-04-27", week_current_end: str = "2025-05-03",
                       week_previous_start: str = "2025-04-20", week_previous_end: str = "2025-04-26",
                       month_current: str = "2025-04", month_previous: str = "2025-03") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    # Log comparison dates for debugging
    logger.debug(f"Running comparisons with the following dates:")
    logger.debug(f"Day: {day_current_date} vs {day_previous_date}")
    logger.debug(f"Week: {week_current_start}-{week_current_end} vs {week_previous_start}-{week_previous_end}")
    logger.debug(f"Month: {month_current} vs {month_previous}")
    """
    Get recent day, week, and month comparisons using fixed dates from configuration.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        day_current_date: Current day date string (YYYY-MM-DD)
        day_previous_date: Previous day date string (YYYY-MM-DD)
        week_current_start: Current week start date string (YYYY-MM-DD)
        week_current_end: Current week end date string (YYYY-MM-DD)
        week_previous_start: Previous week start date string (YYYY-MM-DD)
        week_previous_end: Previous week end date string (YYYY-MM-DD)
        month_current: Current month string (YYYY-MM)
        month_previous: Previous month string (YYYY-MM)
        
    Returns:
        Tuple containing:
        - DataFrame with day comparisons
        - DataFrame with week comparisons
        - DataFrame with month comparisons
        - Dictionary with date strings for the template
    """
    # Day-to-day comparison based on fixed dates
    day_query = load_sql_query("day_comparison", 
                             project_id=project_id, 
                             dataset=dataset, 
                             table=table, 
                             day_current=day_current_date,
                             day_previous=day_previous_date)
    
    day_comparison = run_query(client, day_query)
    
    # Week-to-week comparison based on fixed dates
    week_query = load_sql_query("week_comparison", 
                              project_id=project_id, 
                              dataset=dataset, 
                              table=table,
                              this_week_start=week_current_start,
                              this_week_end=week_current_end,
                              prev_week_start=week_previous_start,
                              prev_week_end=week_previous_end)
    
    week_comparison = run_query(client, week_query)
    
    # Month-to-month comparison based on fixed months
    # Parse month strings to get start and end dates
    this_month_year, this_month_month = map(int, month_current.split('-'))
    prev_month_year, prev_month_month = map(int, month_previous.split('-'))
    
    logger.info(f"Calculating month ranges:")
    logger.info(f"Current month: {month_current} (Year: {this_month_year}, Month: {this_month_month})")
    logger.info(f"Previous month: {month_previous} (Year: {prev_month_year}, Month: {prev_month_month})")
    
    # First day of each month
    this_month_start = f"{month_current}-01"
    prev_month_start = f"{month_previous}-01"
    
    logger.info(f"Month start dates: Current={this_month_start}, Previous={prev_month_start}")
    
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
    
    logger.info(f"Month end dates: Current={this_month_end}, Previous={prev_month_end}")
    logger.info(f"Full month ranges: Current={this_month_start} to {this_month_end}, Previous={prev_month_start} to {prev_month_end}")
    
    month_query = load_sql_query("month_comparison", 
                               project_id=project_id, 
                               dataset=dataset, 
                               table=table,
                               this_month_start=this_month_start,
                               this_month_end=this_month_end,
                               prev_month_start=prev_month_start,
                               prev_month_end=prev_month_end)
    
    month_comparison = run_query(client, month_query)
    
    # Create formatted month names for display
    this_month_display = datetime(this_month_year, this_month_month, 1).strftime('%b %Y')
    prev_month_display = datetime(prev_month_year, prev_month_month, 1).strftime('%b %Y')
    
    # Create a dictionary with date information for the template
    date_info = {
        'day_current_date': day_current_date,
        'day_previous_date': day_previous_date,
        'week_current_date_range': f"{datetime.strptime(week_current_start, '%Y-%m-%d').strftime('%b %d')} - {datetime.strptime(week_current_end, '%Y-%m-%d').strftime('%b %d, %Y')}",
        'week_previous_date_range': f"{datetime.strptime(week_previous_start, '%Y-%m-%d').strftime('%b %d')} - {datetime.strptime(week_previous_end, '%Y-%m-%d').strftime('%b %d, %Y')}",
        'month_current_date_range': this_month_display,
        'month_previous_date_range': prev_month_display
    }
    
    # Always use the provided day_current_date
    date_info['day_current_date'] = day_current_date 
            
    # If we have special date fields in week comparison, use them
    if not week_comparison.empty:
        if 'this_week_start' in week_comparison.columns and 'this_week_end' in week_comparison.columns:
            this_week_start = week_comparison['this_week_start'].iloc[0]
            this_week_end = week_comparison['this_week_end'].iloc[0]
            if this_week_start and this_week_end:
                date_info['week_current_date_range'] = f"{this_week_start} - {this_week_end}"
                
        if 'prev_week_start' in week_comparison.columns and 'prev_week_end' in week_comparison.columns:
            prev_week_start = week_comparison['prev_week_start'].iloc[0]
            prev_week_end = week_comparison['prev_week_end'].iloc[0]
            if prev_week_start and prev_week_end:
                date_info['week_previous_date_range'] = f"{prev_week_start} - {prev_week_end}"
                
    # If we have month fields in the month comparison, use them
    if not month_comparison.empty:
        if 'this_month' in month_comparison.columns:
            this_month = month_comparison['this_month'].iloc[0]
            if this_month:
                date_info['month_current_date_range'] = this_month
                
        if 'prev_month' in month_comparison.columns:
            prev_month = month_comparison['prev_month'].iloc[0]
            if prev_month:
                date_info['month_previous_date_range'] = prev_month
    
    return day_comparison, week_comparison, month_comparison, date_info

def get_product_costs(client: bigquery.Client, project_id: str, dataset: str, table: str, 
                  top_n: int = 10, nonprod_pct_threshold: int = 30) -> pd.DataFrame:
    """
    Get costs by product ID with prod/nonprod breakdown.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        top_n: Number of top products to return
        nonprod_pct_threshold: Threshold for nonprod percentage to highlight
        
    Returns:
        DataFrame with product costs
    """
    query = load_sql_query("product_costs", 
                          project_id=project_id, 
                          dataset=dataset, 
                          table=table,
                          top_n=top_n)
    
    return run_query(client, query)

def get_cto_costs(client: bigquery.Client, project_id: str, dataset: str, table: str, 
                 top_n: int = 10) -> pd.DataFrame:
    """
    Get costs by CTO organization with prod/nonprod breakdown.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        top_n: Number of top CTO organizations to return
        
    Returns:
        DataFrame with CTO organization costs
    """
    query = load_sql_query("cto_costs", 
                          project_id=project_id, 
                          dataset=dataset, 
                          table=table,
                          top_n=top_n)
    
    return run_query(client, query)

def get_pillar_costs(client: bigquery.Client, project_id: str, dataset: str, table: str, 
                   top_n: int = 10) -> pd.DataFrame:
    """
    Get costs by product pillar team with prod/nonprod breakdown.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        top_n: Number of top pillars to return
        
    Returns:
        DataFrame with pillar costs
    """
    query = load_sql_query("pillar_costs", 
                          project_id=project_id, 
                          dataset=dataset, 
                          table=table,
                          top_n=top_n)
    
    return run_query(client, query)

def get_daily_trend_data(client: bigquery.Client, project_id: str, dataset: str, avg_table: str, days: int = 90) -> pd.DataFrame:
    """
    Get daily trend data from avg_daily_cost_table.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        avg_table: BigQuery avg_daily_cost_table name
        days: Number of days to include in the trend
        
    Returns:
        DataFrame with daily trend data
    """
    end_date = datetime.now().date() - timedelta(days=3)  # Latest available data
    start_date = end_date - timedelta(days=days)
    
    query = load_sql_query("daily_trend_data", 
                          project_id=project_id, 
                          dataset=dataset, 
                          avg_table=avg_table,
                          start_date=start_date.strftime('%Y-%m-%d'),
                          end_date=end_date.strftime('%Y-%m-%d'))
    
    return run_query(client, query)