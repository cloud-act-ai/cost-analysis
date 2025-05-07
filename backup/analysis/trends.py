"""
Methods for analyzing cost trends over time.
"""
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from google.cloud import bigquery
from typing import Dict, List, Tuple, Optional, Any

from analysis.core import execute_query, get_month_name, apply_forecast

def get_daily_trend(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    start_date: str,
    end_date: str,
    group_by: Optional[str] = None,
    forecast_days: int = 0
) -> Dict[str, Any]:
    """
    Get daily cost trend over a specified date range.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        group_by: Optional field to group by (e.g., 'environment', 'cloud')
        forecast_days: Number of days to forecast (0 for no forecast)
        
    Returns:
        Dict with trend data and optional forecast
    """
    # Parse dates to validate and extract year/month components
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Build base query
    base_query = f"""
    SELECT
        DATE(CAST(year AS STRING) || '-' || CAST(month AS STRING) || '-01') AS date,
        {'environment,' if group_by == 'environment' else ''}
        {'cloud,' if group_by == 'cloud' else ''}
        {'tr_product_pillar_team,' if group_by == 'tr_product_pillar_team' else ''}
        {'tr_product,' if group_by == 'tr_product' else ''}
        {'managed_service,' if group_by == 'managed_service' else ''}
        SUM(cost) AS total_cost,
        AVG(cost) AS avg_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE (year > {start.year} OR (year = {start.year} AND month >= {start.month}))
        AND (year < {end.year} OR (year = {end.year} AND month <= {end.month}))
    """
    
    # Add grouping if specified
    if group_by:
        query = base_query + f"GROUP BY date, {group_by} ORDER BY date, {group_by}"
    else:
        query = base_query + "GROUP BY date ORDER BY date"
    
    # Execute query
    results = execute_query(client, query)
    
    # Convert date to datetime
    results['date'] = pd.to_datetime(results['date'])
    
    # Format environment labels if grouping by environment
    if group_by == 'environment':
        results[group_by] = results[group_by].apply(
            lambda x: 'Production' if x == 'p' else 'Non-Production' if x == 'np' else x
        )
    
    # Apply forecasting if requested
    if forecast_days > 0:
        if group_by:
            # Apply forecasting for each group
            groups = []
            for name, group in results.groupby(group_by):
                forecast_group = apply_forecast(group, forecast_days)
                groups.append(forecast_group)
            
            # Combine forecasts
            forecast_results = pd.concat(groups, ignore_index=True)
        else:
            # Apply forecasting for the entire dataset
            forecast_results = apply_forecast(results, forecast_days)
        
        results = forecast_results
    
    # Format the response based on grouping
    if group_by:
        trends = []
        for name, group in results.groupby(group_by):
            trend_data = {
                'name': name,
                'data': group.to_dict(orient='records')
            }
            trends.append(trend_data)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'group_by': group_by,
            'trends': trends,
            'has_forecast': forecast_days > 0
        }
    else:
        return {
            'start_date': start_date,
            'end_date': end_date,
            'trend': results.to_dict(orient='records'),
            'has_forecast': forecast_days > 0
        }

def get_monthly_trend(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    group_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get monthly cost trend over a specified period.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        start_year: Start year
        start_month: Start month (1-12)
        end_year: End year
        end_month: End month (1-12)
        group_by: Optional field to group by (e.g., 'environment', 'cloud')
        
    Returns:
        Dict with trend data
    """
    # Build base query
    base_query = f"""
    SELECT
        year,
        month,
        {'environment,' if group_by == 'environment' else ''}
        {'cloud,' if group_by == 'cloud' else ''}
        {'tr_product_pillar_team,' if group_by == 'tr_product_pillar_team' else ''}
        {'tr_product,' if group_by == 'tr_product' else ''}
        {'managed_service,' if group_by == 'managed_service' else ''}
        SUM(cost) AS total_cost,
        AVG(cost) AS avg_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE (year > {start_year} OR (year = {start_year} AND month >= {start_month}))
        AND (year < {end_year} OR (year = {end_year} AND month <= {end_month}))
    """
    
    # Add grouping if specified
    if group_by:
        query = base_query + f"GROUP BY year, month, {group_by} ORDER BY year, month, {group_by}"
    else:
        query = base_query + "GROUP BY year, month ORDER BY year, month"
    
    # Execute query
    results = execute_query(client, query)
    
    # Add month_name column
    results['month_name'] = results['month'].apply(get_month_name)
    results['period'] = results.apply(lambda row: f"{row['month_name']} {row['year']}", axis=1)
    
    # Format environment labels if grouping by environment
    if group_by == 'environment':
        results[group_by] = results[group_by].apply(
            lambda x: 'Production' if x == 'p' else 'Non-Production' if x == 'np' else x
        )
    
    # Format the response based on grouping
    if group_by:
        trends = []
        for name, group in results.groupby(group_by):
            trend_data = {
                'name': name,
                'data': group.to_dict(orient='records')
            }
            trends.append(trend_data)
        
        return {
            'start_period': f"{get_month_name(start_month)} {start_year}",
            'end_period': f"{get_month_name(end_month)} {end_year}",
            'group_by': group_by,
            'trends': trends
        }
    else:
        return {
            'start_period': f"{get_month_name(start_month)} {start_year}",
            'end_period': f"{get_month_name(end_month)} {end_year}",
            'trend': results.to_dict(orient='records')
        }

def get_product_team_trend(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    start_date: str,
    end_date: str,
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Get cost trend for top product pillar teams.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        top_n: Number of top teams to include
        
    Returns:
        Dict with trend data for top teams
    """
    # Parse dates to validate and extract year/month components
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # First, get the top N product pillar teams by total cost
    top_teams_query = f"""
    SELECT
        tr_product_pillar_team,
        SUM(cost) AS total_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE (year > {start.year} OR (year = {start.year} AND month >= {start.month}))
        AND (year < {end.year} OR (year = {end.year} AND month <= {end.month}))
    GROUP BY tr_product_pillar_team
    ORDER BY total_cost DESC
    LIMIT {top_n}
    """
    
    top_teams = execute_query(client, top_teams_query)
    
    if top_teams.empty:
        return {
            'start_date': start_date,
            'end_date': end_date,
            'teams': []
        }
    
    # Get the team names
    team_names = top_teams['tr_product_pillar_team'].tolist()
    team_names_str = "', '".join(team_names)
    
    # Now get daily cost data for the top teams
    daily_query = f"""
    SELECT
        DATE(CAST(year AS STRING) || '-' || CAST(month AS STRING) || '-01') AS date,
        tr_product_pillar_team,
        SUM(cost) AS total_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE (year > {start.year} OR (year = {start.year} AND month >= {start.month}))
        AND (year < {end.year} OR (year = {end.year} AND month <= {end.month}))
        AND tr_product_pillar_team IN ('{team_names_str}')
    GROUP BY date, tr_product_pillar_team
    ORDER BY date, tr_product_pillar_team
    """
    
    daily_results = execute_query(client, daily_query)
    
    # Convert date to datetime
    daily_results['date'] = pd.to_datetime(daily_results['date'])
    
    # Format the response with trend data for each team
    teams = []
    for team in team_names:
        team_data = daily_results[daily_results['tr_product_pillar_team'] == team]
        teams.append({
            'name': team,
            'total_cost': float(top_teams[top_teams['tr_product_pillar_team'] == team]['total_cost'].values[0]),
            'trend': team_data.to_dict(orient='records')
        })
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'teams': teams
    }