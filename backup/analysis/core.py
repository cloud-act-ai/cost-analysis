"""
Core utilities for FinOps analysis.
"""
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from google.cloud import bigquery
from typing import Dict, List, Tuple, Optional, Any, Union

def get_bigquery_client(project_id: str) -> bigquery.Client:
    """
    Get a BigQuery client for the given project.
    
    Args:
        project_id: Google Cloud project ID
        
    Returns:
        A BigQuery client
    """
    return bigquery.Client(project=project_id)

def execute_query(client: bigquery.Client, query: str) -> pd.DataFrame:
    """
    Execute a BigQuery query and return the results as a DataFrame.
    
    Args:
        client: BigQuery client
        query: SQL query to execute
        
    Returns:
        DataFrame with query results
    """
    return client.query(query).to_dataframe()

def get_date_range(start_date: str, end_date: str) -> List[datetime]:
    """
    Generate a list of dates between start_date and end_date.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        List of datetime objects for each day in the range
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = []
    
    current = start
    while current <= end:
        date_range.append(current)
        current += timedelta(days=1)
    
    return date_range

def get_month_name(month: int) -> str:
    """
    Convert month number to month name.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Month name (Jan, Feb, etc.)
    """
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    return month_names.get(month, f"Month {month}")

def calculate_growth(current: float, previous: float) -> float:
    """
    Calculate percentage growth between two values.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Growth percentage (positive means growth, negative means decline)
    """
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    
    return ((current - previous) / previous) * 100.0

def apply_forecast(data: pd.DataFrame, forecast_days: int = 90) -> pd.DataFrame:
    """
    Apply simple linear regression forecasting to the given data.
    
    Args:
        data: DataFrame with date and cost columns
        forecast_days: Number of days to forecast
        
    Returns:
        DataFrame with original data and forecast appended
    """
    if len(data) < 10:
        # Not enough data for reliable forecasting
        return data
    
    # Sort by date to ensure proper sequence
    data = data.sort_values('date')
    
    # Use numpy to create a linear model
    x = np.arange(len(data))
    y = data['cost'].values
    
    # Create linear fit
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    
    # Create future dates
    last_date = pd.to_datetime(data['date'].max())
    future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
    
    # Predict values for future dates
    future_values = p(np.arange(len(data), len(data) + forecast_days))
    
    # Create forecast DataFrame
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'cost': future_values,
        'is_forecast': True
    })
    
    # Add is_forecast column to original data
    data['is_forecast'] = False
    
    # Combine original data and forecast
    result = pd.concat([data, forecast_df], ignore_index=True)
    
    return result