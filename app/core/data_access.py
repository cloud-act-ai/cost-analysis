"""
Asynchronous data access functions for FinOps360 cost analysis FastAPI dashboard.
"""
import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Any, Optional

import pandas as pd
from google.cloud import bigquery
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.utils.db import run_query, load_sql_query
from app.utils.data_generator import (
    create_sample_ytd_costs,
    create_sample_fy26_ytd_costs,
    create_sample_fy26_costs,
    create_sample_fy25_costs,
    create_sample_day_comparison,
    create_sample_week_comparison,
    create_sample_month_comparison,
    create_sample_product_costs,
    create_sample_cto_costs,
    create_sample_pillar_costs,
    create_sample_daily_trend_data
)

logger = logging.getLogger(__name__)

# Thread pool for running BigQuery queries in async functions
_thread_pool = ThreadPoolExecutor(max_workers=5)

async def get_ytd_costs_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get year-to-date costs for production and non-production (async version).
    """
    query = load_sql_query(
        "ytd_costs", 
        project_id=project_id, 
        dataset=dataset, 
        table=table,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )
    
    try:
        # Run the query in a thread to not block the event loop
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_ytd_costs_async: {e}")
        # Return sample data on error
        return create_sample_ytd_costs()

async def get_fy26_ytd_costs_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get FY26 year-to-date costs for production and non-production (async version).
    This represents actual costs from the beginning of FY26 (2025-02-01) to current date - 3 days.
    """
    query = load_sql_query(
        "fy26_ytd_costs", 
        project_id=project_id, 
        dataset=dataset, 
        table=table,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_fy26_ytd_costs_async: {e}")
        return create_sample_fy26_ytd_costs()

async def get_fy26_costs_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get projected FY26 costs for production and non-production (async version).
    """
    query = load_sql_query(
        "fy26_costs", 
        project_id=project_id, 
        dataset=dataset, 
        table=table,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_fy26_costs_async: {e}")
        return create_sample_fy26_costs()

async def get_fy25_costs_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get FY25 costs for year-over-year comparison (async version).
    """
    query = load_sql_query(
        "fy25_costs", 
        project_id=project_id, 
        dataset=dataset, 
        table=table,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_fy25_costs_async: {e}")
        return create_sample_fy25_costs()

async def get_recent_comparisons_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str,
    day_current_date: str = "2025-05-03", 
    day_previous_date: str = "2025-05-02",
    week_current_start: str = "2025-04-27", 
    week_current_end: str = "2025-05-03",
    week_previous_start: str = "2025-04-20", 
    week_previous_end: str = "2025-04-26",
    month_current: str = "2025-04", 
    month_previous: str = "2025-03",
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    """
    Get recent day, week, and month comparisons using fixed dates from configuration (async version).
    """
    # Log comparison dates for debugging
    logger.debug(f"Running comparisons with the following dates:")
    logger.debug(f"Day: {day_current_date} vs {day_previous_date}")
    logger.debug(f"Week: {week_current_start}-{week_current_end} vs {week_previous_start}-{week_previous_end}")
    logger.debug(f"Month: {month_current} vs {month_previous}")
    
    try:
        # Day comparison
        day_query = load_sql_query(
            "day_comparison",
            project_id=project_id,
            dataset=dataset,
            table=table,
            day_current=day_current_date,
            day_previous=day_previous_date,
            cto_filter=cto_filter,
            pillar_filter=pillar_filter,
            product_filter=product_filter
        )
        
        # Week comparison
        week_query = load_sql_query(
            "week_comparison",
            project_id=project_id,
            dataset=dataset,
            table=table,
            this_week_start=week_current_start,
            this_week_end=week_current_end,
            prev_week_start=week_previous_start,
            prev_week_end=week_previous_end,
            cto_filter=cto_filter,
            pillar_filter=pillar_filter,
            product_filter=product_filter
        )
        
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
        
        # Month comparison query
        month_query = load_sql_query(
            "month_comparison",
            project_id=project_id,
            dataset=dataset,
            table=table,
            this_month_start=this_month_start,
            this_month_end=this_month_end,
            prev_month_start=prev_month_start,
            prev_month_end=prev_month_end,
            cto_filter=cto_filter,
            pillar_filter=pillar_filter,
            product_filter=product_filter
        )
        
        # Run all queries in parallel using thread pool
        day_task = asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, day_query)
        )
        
        week_task = asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, week_query)
        )
        
        month_task = asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, month_query)
        )
        
        # Wait for all queries to complete
        day_comparison, week_comparison, month_comparison = await asyncio.gather(
            day_task, week_task, month_task
        )
        
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
    
    except Exception as e:
        logger.error(f"Error in get_recent_comparisons_async: {e}")
        # Return sample data on error
        sample_day = create_sample_day_comparison()
        sample_week = create_sample_week_comparison()
        sample_month = create_sample_month_comparison()
        
        # Create a dictionary with basic date information
        date_info = {
            'day_current_date': day_current_date,
            'day_previous_date': day_previous_date,
            'week_current_date_range': f"Week of {week_current_start}",
            'week_previous_date_range': f"Week of {week_previous_start}",
            'month_current_date_range': month_current,
            'month_previous_date_range': month_previous
        }
        
        return sample_day, sample_week, sample_month, date_info

async def get_product_costs_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str, 
    top_n: int = 10, 
    nonprod_pct_threshold: int = 30,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get costs by product ID with prod/nonprod breakdown (async version).
    """
    query = load_sql_query(
        "product_costs", 
        project_id=project_id, 
        dataset=dataset, 
        table=table,
        top_n=top_n,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_product_costs_async: {e}")
        return create_sample_product_costs()

async def get_cto_costs_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str, 
    top_n: int = 10,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get costs by CTO organization with prod/nonprod breakdown (async version).
    """
    query = load_sql_query(
        "cto_costs", 
        project_id=project_id, 
        dataset=dataset, 
        table=table,
        top_n=top_n,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_cto_costs_async: {e}")
        return create_sample_cto_costs()

async def get_pillar_costs_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    table: str, 
    top_n: int = 10,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get costs by product pillar team with prod/nonprod breakdown (async version).
    """
    query = load_sql_query(
        "pillar_costs", 
        project_id=project_id, 
        dataset=dataset, 
        table=table,
        top_n=top_n,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_pillar_costs_async: {e}")
        return create_sample_pillar_costs()

async def get_daily_trend_data_async(
    client: bigquery.Client, 
    project_id: str, 
    dataset: str, 
    avg_table: str, 
    days: int = 90,
    cto_filter: str = "",
    pillar_filter: str = "",
    product_filter: str = ""
) -> pd.DataFrame:
    """
    Get daily trend data from avg_table (async version).
    """
    # Get date range from config
    from app.utils.config_loader import load_config
    config = load_config("config.yaml")
    data_config = config.get('data', {})
    
    # Get fiscal year start and end dates from config
    fy_start_date_str = data_config.get('fy_start_date', '')
    fy_end_date_str = data_config.get('fy_end_date', '')
    
    # Use the date strings directly in the SQL query
    # No need to convert to date objects since SQL uses date strings
    start_date_str = fy_start_date_str
    end_date_str = fy_end_date_str
    
    query = load_sql_query(
        "daily_trend_data",
        project_id=project_id,
        dataset=dataset,
        avg_table=avg_table,
        start_date=start_date_str,
        end_date=end_date_str,
        cto_filter=cto_filter,
        pillar_filter=pillar_filter,
        product_filter=product_filter
    )

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            _thread_pool, 
            lambda: run_query(client, query)
        )
        return result
    except Exception as e:
        logger.error(f"Error in get_daily_trend_data_async: {e}")
        return create_sample_daily_trend_data()

# Helper function to create a sample date_info dictionary
def create_sample_date_info() -> Dict[str, str]:
    """Create sample date information for templates when real data is unavailable."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # Calculate current and previous weeks
    current_week_end = today - timedelta(days=today.weekday() + 1)  # Last Sunday
    current_week_start = current_week_end - timedelta(days=6)  # Last Monday
    previous_week_end = current_week_start - timedelta(days=1)  # Sunday before last
    previous_week_start = previous_week_end - timedelta(days=6)  # Monday before last
    
    # Calculate current and previous months
    current_month = today.replace(day=1)
    previous_month = (current_month - timedelta(days=1)).replace(day=1)
    
    return {
        'day_current_date': today.strftime('%Y-%m-%d'),
        'day_previous_date': yesterday.strftime('%Y-%m-%d'),
        'week_current_date_range': f"{current_week_start.strftime('%b %d')} - {current_week_end.strftime('%b %d, %Y')}",
        'week_previous_date_range': f"{previous_week_start.strftime('%b %d')} - {previous_week_end.strftime('%b %d, %Y')}",
        'month_current_date_range': current_month.strftime('%b %Y'),
        'month_previous_date_range': previous_month.strftime('%b %Y')
    }