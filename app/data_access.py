"""
Data access functions for FinOps360 cost analysis dashboard.
"""
import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Any, Optional

import pandas as pd
from google.cloud import bigquery

from app.utils.bigquery import run_query

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
    query = f"""
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS ytd_cost,
        COUNT(DISTINCT date) AS days
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3
    GROUP BY environment_type
    """
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
    query = f"""
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost,
        COUNT(DISTINCT date) AS days
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '2025-02-01' AND '2026-01-31'
    GROUP BY environment_type
    """
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
    query = f"""
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost,
        COUNT(DISTINCT date) AS days
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '2024-02-01' AND '2025-01-31'
    GROUP BY environment_type
    """
    return run_query(client, query)

def get_recent_comparisons(client: bigquery.Client, project_id: str, dataset: str, table: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Get recent day, week, and month comparisons.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        
    Returns:
        Tuple of DataFrames with day, week, and month comparisons
    """
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)
    
    # Day-to-day comparison (4 days ago vs 5 days ago)
    day4 = today - timedelta(days=4)
    day5 = today - timedelta(days=5)
    
    day_query = f"""
    WITH day4 AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date = '{day4}'
        GROUP BY environment_type
    ),
    day5 AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date = '{day5}'
        GROUP BY environment_type
    )
    SELECT
        d4.environment_type,
        d4.total_cost AS day4_cost,
        d5.total_cost AS day5_cost,
        (d4.total_cost - d5.total_cost) / NULLIF(d5.total_cost, 0) * 100 AS percent_change
    FROM day4 d4
    JOIN day5 d5 ON d4.environment_type = d5.environment_type
    """
    day_comparison = run_query(client, day_query)
    
    # Week-to-week comparison
    this_week_start = today - timedelta(days=today.weekday() + 7)  # Last week's start
    this_week_end = this_week_start + timedelta(days=6)
    prev_week_start = this_week_start - timedelta(days=7)
    prev_week_end = prev_week_start + timedelta(days=6)
    
    week_query = f"""
    WITH this_week AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{this_week_start}' AND '{this_week_end}'
        GROUP BY environment_type
    ),
    prev_week AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{prev_week_start}' AND '{prev_week_end}'
        GROUP BY environment_type
    )
    SELECT
        tw.environment_type,
        tw.total_cost AS this_week_cost,
        pw.total_cost AS prev_week_cost,
        (tw.total_cost - pw.total_cost) / NULLIF(pw.total_cost, 0) * 100 AS percent_change
    FROM this_week tw
    JOIN prev_week pw ON tw.environment_type = pw.environment_type
    """
    week_comparison = run_query(client, week_query)
    
    # Month-to-month comparison
    this_month = today.replace(day=1)
    prev_month = (this_month.replace(day=1) - timedelta(days=1)).replace(day=1)
    this_month_end = today
    days_in_prev_month = (this_month - timedelta(days=1)).day
    prev_month_end = prev_month.replace(day=min(this_month_end.day, days_in_prev_month))
    
    month_query = f"""
    WITH this_month AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{this_month}' AND '{this_month_end}'
        GROUP BY environment_type
    ),
    prev_month AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{prev_month}' AND '{prev_month_end}'
        GROUP BY environment_type
    )
    SELECT
        tm.environment_type,
        tm.total_cost AS this_month_cost,
        pm.total_cost AS prev_month_cost,
        (tm.total_cost - pm.total_cost) / NULLIF(pm.total_cost, 0) * 100 AS percent_change
    FROM this_month tm
    JOIN prev_month pm ON tm.environment_type = pm.environment_type
    """
    month_comparison = run_query(client, month_query)
    
    return day_comparison, week_comparison, month_comparison

def get_product_costs(client: bigquery.Client, project_id: str, dataset: str, table: str) -> pd.DataFrame:
    """
    Get costs by product ID with prod/nonprod breakdown.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        
    Returns:
        DataFrame with product costs
    """
    query = f"""
    WITH product_costs AS (
        SELECT
            tr_product_id AS product_id,
            tr_product AS product_name,
            tr_product_pillar_team AS pillar_team,
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment,
            SUM(cost) AS ytd_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3
        GROUP BY product_id, product_name, pillar_team, environment
    ),
    prod_costs AS (
        SELECT
            product_id,
            product_name,
            pillar_team,
            ytd_cost AS prod_ytd_cost
        FROM product_costs
        WHERE environment = 'PROD'
    ),
    nonprod_costs AS (
        SELECT
            product_id,
            product_name,
            pillar_team,
            ytd_cost AS nonprod_ytd_cost
        FROM product_costs
        WHERE environment = 'NON-PROD'
    ),
    combined_costs AS (
        SELECT
            COALESCE(p.product_id, np.product_id) AS product_id,
            COALESCE(p.product_name, np.product_name) AS product_name,
            COALESCE(p.pillar_team, np.pillar_team) AS pillar_team,
            COALESCE(p.prod_ytd_cost, 0) AS prod_ytd_cost,
            COALESCE(np.nonprod_ytd_cost, 0) AS nonprod_ytd_cost,
            COALESCE(p.prod_ytd_cost, 0) + COALESCE(np.nonprod_ytd_cost, 0) AS total_ytd_cost
        FROM prod_costs p
        FULL OUTER JOIN nonprod_costs np ON p.product_id = np.product_id
    )
    SELECT
        product_id,
        product_name,
        pillar_team,
        prod_ytd_cost,
        nonprod_ytd_cost,
        total_ytd_cost,
        CASE 
            WHEN total_ytd_cost > 0 THEN (nonprod_ytd_cost / total_ytd_cost) * 100
            ELSE 0
        END AS nonprod_percentage
    FROM combined_costs
    WHERE total_ytd_cost > 0
    ORDER BY total_ytd_cost DESC
    LIMIT 50
    """
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
    
    query = f"""
    SELECT
        date,
        environment_type,
        daily_cost,
        fy25_avg_daily_spend,
        fy26_ytd_avg_daily_spend,
        fy26_forecasted_avg_daily_spend
    FROM `{project_id}.{dataset}.{avg_table}`
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date
    """
    return run_query(client, query)