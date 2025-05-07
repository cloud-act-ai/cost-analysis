"""
Methods for comparing cost data across different time periods.
"""
from datetime import datetime, timedelta
import pandas as pd
from google.cloud import bigquery
from typing import Dict, Tuple, Optional, List, Any

from analysis.core import execute_query, get_month_name, calculate_growth

def compare_days(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    day1: str,
    day2: str
) -> Dict[str, Any]:
    """
    Compare cloud costs between two specific days.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        day1: First day (YYYY-MM-DD)
        day2: Second day (YYYY-MM-DD)
        
    Returns:
        Dict with comparison results
    """
    # Parse days to validate and extract year/month components
    day1_date = datetime.strptime(day1, "%Y-%m-%d")
    day2_date = datetime.strptime(day2, "%Y-%m-%d")
    
    # Ensure day1 is always the earlier date
    if day1_date > day2_date:
        day1_date, day2_date = day2_date, day1_date
        day1, day2 = day2, day1
    
    # Extract year and month for each day
    day1_year = day1_date.year
    day1_month = day1_date.month
    day2_year = day2_date.year
    day2_month = day2_date.month
    
    # Build query to get costs for both days by environment
    query = f"""
    WITH day1_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE year = {day1_year} AND month = {day1_month} 
            AND EXTRACT(DAY FROM DATE(CAST(year AS STRING) || '-' || 
                CAST(month AS STRING) || '-01')) = {day1_date.day}
        GROUP BY environment
    ),
    day2_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE year = {day2_year} AND month = {day2_month}
            AND EXTRACT(DAY FROM DATE(CAST(year AS STRING) || '-' || 
                CAST(month AS STRING) || '-01')) = {day2_date.day}
        GROUP BY environment
    )
    SELECT
        COALESCE(d1.environment, d2.environment) AS environment,
        COALESCE(d1.total_cost, 0) AS day1_cost,
        COALESCE(d2.total_cost, 0) AS day2_cost,
        COALESCE(d2.total_cost, 0) - COALESCE(d1.total_cost, 0) AS cost_change,
        CASE 
            WHEN COALESCE(d1.total_cost, 0) = 0 THEN NULL
            ELSE (COALESCE(d2.total_cost, 0) - COALESCE(d1.total_cost, 0)) / COALESCE(d1.total_cost, 1) * 100
        END AS percent_change
    FROM day1_data d1
    FULL OUTER JOIN day2_data d2
    ON d1.environment = d2.environment
    ORDER BY environment
    """
    
    # Execute query
    results = execute_query(client, query)
    
    # Calculate totals
    day1_total = results['day1_cost'].sum()
    day2_total = results['day2_cost'].sum()
    absolute_change = day2_total - day1_total
    percent_change = calculate_growth(day2_total, day1_total)
    
    # Format the environment labels for better display
    results['environment'] = results['environment'].apply(
        lambda x: 'Production' if x == 'p' else 'Non-Production' if x == 'np' else x
    )
    
    return {
        'day1': day1,
        'day2': day2,
        'day1_total': day1_total,
        'day2_total': day2_total,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'by_environment': results.to_dict(orient='records')
    }

def compare_weeks(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    week1_start: str,
    week2_start: str
) -> Dict[str, Any]:
    """
    Compare cloud costs between two weeks.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        week1_start: Start date of first week (YYYY-MM-DD)
        week2_start: Start date of second week (YYYY-MM-DD)
        
    Returns:
        Dict with comparison results
    """
    # Parse start dates
    week1_start_date = datetime.strptime(week1_start, "%Y-%m-%d")
    week2_start_date = datetime.strptime(week2_start, "%Y-%m-%d")
    
    # Calculate end dates (7 days from start)
    week1_end_date = week1_start_date + timedelta(days=6)
    week2_end_date = week2_start_date + timedelta(days=6)
    
    # Format dates for the query
    week1_end = week1_end_date.strftime("%Y-%m-%d")
    week2_end = week2_end_date.strftime("%Y-%m-%d")
    
    # Build query for weekly comparison
    query = f"""
    WITH week1_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost,
            AVG(cost) AS avg_daily_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE (year = {week1_start_date.year} AND month = {week1_start_date.month})
            OR (year = {week1_end_date.year} AND month = {week1_end_date.month})
        -- Additional date filtering would go here in a real implementation
        GROUP BY environment
    ),
    week2_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost,
            AVG(cost) AS avg_daily_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE (year = {week2_start_date.year} AND month = {week2_start_date.month})
            OR (year = {week2_end_date.year} AND month = {week2_end_date.month})
        -- Additional date filtering would go here in a real implementation
        GROUP BY environment
    )
    SELECT
        COALESCE(w1.environment, w2.environment) AS environment,
        COALESCE(w1.total_cost, 0) AS week1_cost,
        COALESCE(w2.total_cost, 0) AS week2_cost,
        COALESCE(w1.avg_daily_cost, 0) AS week1_avg_daily,
        COALESCE(w2.avg_daily_cost, 0) AS week2_avg_daily,
        COALESCE(w2.total_cost, 0) - COALESCE(w1.total_cost, 0) AS cost_change,
        CASE 
            WHEN COALESCE(w1.total_cost, 0) = 0 THEN NULL
            ELSE (COALESCE(w2.total_cost, 0) - COALESCE(w1.total_cost, 0)) / COALESCE(w1.total_cost, 1) * 100
        END AS percent_change
    FROM week1_data w1
    FULL OUTER JOIN week2_data w2
    ON w1.environment = w2.environment
    ORDER BY environment
    """
    
    # Execute query
    results = execute_query(client, query)
    
    # Calculate totals
    week1_total = results['week1_cost'].sum()
    week2_total = results['week2_cost'].sum()
    absolute_change = week2_total - week1_total
    percent_change = calculate_growth(week2_total, week1_total)
    
    # Format the environment labels for better display
    results['environment'] = results['environment'].apply(
        lambda x: 'Production' if x == 'p' else 'Non-Production' if x == 'np' else x
    )
    
    return {
        'week1_start': week1_start,
        'week1_end': week1_end,
        'week2_start': week2_start,
        'week2_end': week2_end,
        'week1_total': week1_total,
        'week2_total': week2_total,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'by_environment': results.to_dict(orient='records')
    }

def compare_months(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    month1: int,
    year1: int,
    month2: int,
    year2: int
) -> Dict[str, Any]:
    """
    Compare cloud costs between two months.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        month1: First month (1-12)
        year1: First year
        month2: Second month (1-12)
        year2: Second year
        
    Returns:
        Dict with comparison results
    """
    # Build query for monthly comparison
    query = f"""
    WITH month1_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost,
            AVG(cost) AS avg_daily_cost,
            COUNT(DISTINCT CAST(year AS STRING) || '-' || CAST(month AS STRING)) AS day_count
        FROM `{project_id}.{dataset}.{table}`
        WHERE year = {year1} AND month = {month1}
        GROUP BY environment
    ),
    month2_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost,
            AVG(cost) AS avg_daily_cost,
            COUNT(DISTINCT CAST(year AS STRING) || '-' || CAST(month AS STRING)) AS day_count
        FROM `{project_id}.{dataset}.{table}`
        WHERE year = {year2} AND month = {month2}
        GROUP BY environment
    )
    SELECT
        COALESCE(m1.environment, m2.environment) AS environment,
        COALESCE(m1.total_cost, 0) AS month1_cost,
        COALESCE(m2.total_cost, 0) AS month2_cost,
        COALESCE(m1.avg_daily_cost, 0) AS month1_avg_daily,
        COALESCE(m2.avg_daily_cost, 0) AS month2_avg_daily,
        COALESCE(m2.total_cost, 0) - COALESCE(m1.total_cost, 0) AS cost_change,
        CASE 
            WHEN COALESCE(m1.total_cost, 0) = 0 THEN NULL
            ELSE (COALESCE(m2.total_cost, 0) - COALESCE(m1.total_cost, 0)) / COALESCE(m1.total_cost, 1) * 100
        END AS percent_change,
        m1.day_count AS month1_days,
        m2.day_count AS month2_days
    FROM month1_data m1
    FULL OUTER JOIN month2_data m2
    ON m1.environment = m2.environment
    ORDER BY environment
    """
    
    # Execute query
    results = execute_query(client, query)
    
    # Calculate totals
    month1_total = results['month1_cost'].sum()
    month2_total = results['month2_cost'].sum()
    absolute_change = month2_total - month1_total
    percent_change = calculate_growth(month2_total, month1_total)
    
    # Format the environment labels for better display
    results['environment'] = results['environment'].apply(
        lambda x: 'Production' if x == 'p' else 'Non-Production' if x == 'np' else x
    )
    
    # Get month names
    month1_name = get_month_name(month1)
    month2_name = get_month_name(month2)
    
    return {
        'month1': f"{month1_name} {year1}",
        'month2': f"{month2_name} {year2}",
        'month1_total': month1_total,
        'month2_total': month2_total,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'by_environment': results.to_dict(orient='records')
    }

def compare_years(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    year1: int,
    year2: int
) -> Dict[str, Any]:
    """
    Compare cloud costs between two years.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        year1: First year
        year2: Second year
        
    Returns:
        Dict with comparison results
    """
    # Build query for yearly comparison
    query = f"""
    WITH year1_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost,
            AVG(cost) AS avg_daily_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE year = {year1}
        GROUP BY environment
    ),
    year2_data AS (
        SELECT
            environment,
            SUM(cost) AS total_cost,
            AVG(cost) AS avg_daily_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE year = {year2}
        GROUP BY environment
    )
    SELECT
        COALESCE(y1.environment, y2.environment) AS environment,
        COALESCE(y1.total_cost, 0) AS year1_cost,
        COALESCE(y2.total_cost, 0) AS year2_cost,
        COALESCE(y1.avg_daily_cost, 0) AS year1_avg_daily,
        COALESCE(y2.avg_daily_cost, 0) AS year2_avg_daily,
        COALESCE(y2.total_cost, 0) - COALESCE(y1.total_cost, 0) AS cost_change,
        CASE 
            WHEN COALESCE(y1.total_cost, 0) = 0 THEN NULL
            ELSE (COALESCE(y2.total_cost, 0) - COALESCE(y1.total_cost, 0)) / COALESCE(y1.total_cost, 1) * 100
        END AS percent_change
    FROM year1_data y1
    FULL OUTER JOIN year2_data y2
    ON y1.environment = y2.environment
    ORDER BY environment
    """
    
    # Execute query
    results = execute_query(client, query)
    
    # Calculate totals
    year1_total = results['year1_cost'].sum()
    year2_total = results['year2_cost'].sum()
    absolute_change = year2_total - year1_total
    percent_change = calculate_growth(year2_total, year1_total)
    
    # Format the environment labels for better display
    results['environment'] = results['environment'].apply(
        lambda x: 'Production' if x == 'p' else 'Non-Production' if x == 'np' else x
    )
    
    return {
        'year1': str(year1),
        'year2': str(year2),
        'year1_total': year1_total,
        'year2_total': year2_total,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'by_environment': results.to_dict(orient='records')
    }