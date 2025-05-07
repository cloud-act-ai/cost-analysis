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
                       day_offset: int = 4, week_offset: int = 1, month_offset: int = 1) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    """
    Get recent day, week, and month comparisons.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        day_offset: Days ago to use for day comparison
        week_offset: Weeks ago to use for week comparison
        month_offset: Months ago to use for month comparison
        
    Returns:
        Tuple containing:
        - DataFrame with day comparisons
        - DataFrame with week comparisons
        - DataFrame with month comparisons
        - Dictionary with date strings for the template
    """
    today = datetime.now().date()
    
    # Day-to-day comparison based on configured offset
    day_current = today - timedelta(days=day_offset)
    day_previous = today - timedelta(days=day_offset+1)
    
    day_query = load_sql_query("day_comparison", 
                              project_id=project_id, 
                              dataset=dataset, 
                              table=table, 
                              day_current=day_current.strftime('%Y-%m-%d'),
                              day_previous=day_previous.strftime('%Y-%m-%d'))
    
    day_comparison = run_query(client, day_query)
    
    # Week-to-week comparison based on configured offset
    weeks_offset = 7 * week_offset
    this_week_start = today - timedelta(days=today.weekday() + weeks_offset)
    this_week_end = this_week_start + timedelta(days=6)
    prev_week_start = this_week_start - timedelta(days=7)
    prev_week_end = prev_week_start + timedelta(days=6)
    
    week_query = load_sql_query("week_comparison", 
                               project_id=project_id, 
                               dataset=dataset, 
                               table=table,
                               this_week_start=this_week_start.strftime('%Y-%m-%d'),
                               this_week_end=this_week_end.strftime('%Y-%m-%d'),
                               prev_week_start=prev_week_start.strftime('%Y-%m-%d'),
                               prev_week_end=prev_week_end.strftime('%Y-%m-%d'))
    
    week_comparison = run_query(client, week_query)
    
    # Month-to-month comparison based on configured offset
    months_to_subtract = month_offset
    # Get the current month minus offset
    if today.month <= months_to_subtract:
        this_month_year = today.year - 1
        this_month_month = today.month + 12 - months_to_subtract
    else:
        this_month_year = today.year
        this_month_month = today.month - months_to_subtract
        
    this_month = today.replace(year=this_month_year, month=this_month_month, day=1)
    
    # Get the previous month
    if this_month.month == 1:
        prev_month = this_month.replace(year=this_month.year-1, month=12, day=1)
    else:
        prev_month = this_month.replace(month=this_month.month-1, day=1)
        
    # Set end dates
    this_month_end = (prev_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    this_month_end = min(this_month_end, today)  # Don't go past today
    days_in_prev_month = (prev_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    prev_month_end = prev_month.replace(day=min(this_month_end.day, days_in_prev_month.day))
    
    month_query = load_sql_query("month_comparison", 
                                project_id=project_id, 
                                dataset=dataset, 
                                table=table,
                                this_month_start=this_month.strftime('%Y-%m-%d'),
                                this_month_end=this_month_end.strftime('%Y-%m-%d'),
                                prev_month_start=prev_month.strftime('%Y-%m-%d'),
                                prev_month_end=prev_month_end.strftime('%Y-%m-%d'))
    
    month_comparison = run_query(client, month_query)
    
    # Create a dictionary with date information for the template
    date_info = {
        'day_current_date': day_current.strftime('%Y-%m-%d'),
        'day_previous_date': day_previous.strftime('%Y-%m-%d'),
        'week_current_date_range': f"{this_week_start.strftime('%b %d')} - {this_week_end.strftime('%b %d, %Y')}",
        'week_previous_date_range': f"{prev_week_start.strftime('%b %d')} - {prev_week_end.strftime('%b %d, %Y')}",
        'month_current_date_range': f"{this_month.strftime('%b %Y')}",
        'month_previous_date_range': f"{prev_month.strftime('%b %Y')}"
    }
    
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