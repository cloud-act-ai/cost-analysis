"""
BigQuery integration for daily average cost data.
"""
import pandas as pd
import os
import logging
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from typing import Optional, List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def load_avg_daily_data(
    project_id: str,
    dataset: str,
    table: str,
    credentials_path: Optional[str] = None,
    use_bqdf: bool = True,
    columns: Optional[List[str]] = None,
    environment_filter: Optional[str] = None,
    cto_filter: Optional[str] = None,
    date_filter: Optional[str] = None
) -> pd.DataFrame:
    """
    Load data from the average daily cost BigQuery table.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        credentials_path: Path to GCP credentials JSON file
        use_bqdf: Whether to use BigQuery DataFrames for improved performance
        columns: List of columns to select (None for all columns)
        environment_filter: Optional filter for environment_type column
        cto_filter: Optional filter for cto column
        date_filter: Optional filter for date column (format: 'YYYY-MM-DD')
        
    Returns:
        DataFrame with the average daily cost data
    """
    # Set up credentials if provided
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=project_id)
        
        # Build query
        column_projection = ", ".join(columns) if columns else "*"
        query = f"SELECT {column_projection} FROM `{project_id}.{dataset}.{table}`"
        
        # Add filters if provided
        filters = []
        if environment_filter:
            filters.append(f"LOWER(environment_type) = LOWER('{environment_filter}')")
        if cto_filter:
            filters.append(f"cto = '{cto_filter}'")
        if date_filter:
            filters.append(f"date = '{date_filter}'")
        
        if filters:
            query += " WHERE " + " AND ".join(filters)
        
        # Add order by clause
        query += " ORDER BY date DESC"
        
        # Execute query using BigQuery DataFrames if selected
        if use_bqdf:
            df = client.query(query).to_dataframe(create_bqstorage_client=True)
        else:
            df = client.query(query).to_dataframe()
        
        # Convert date column to datetime if it exists
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
        
    except GoogleCloudError as e:
        logger.error(f"Google Cloud error: {e}")
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error loading average daily cost data: {e}")
        return pd.DataFrame()

def get_fiscal_year_comparison(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    environment_type: Optional[str] = None,
    cto: Optional[str] = None,
    limit: int = 10
) -> pd.DataFrame:
    """
    Get fiscal year comparison data from the fiscal_year_comparison view.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        environment_type: Optional filter for environment column
        cto: Optional filter for cto column
        limit: Maximum number of rows to return
        
    Returns:
        DataFrame with fiscal year comparison data
    """
    try:
        # Build query using the fiscal_year_comparison view
        query = f"""
        SELECT
          date,
          environment,
          cto,
          fy24_avg_daily_spend,
          fy25_avg_daily_spend,
          fy26_avg_daily_spend,
          current_cost,
          COALESCE(current_cost / NULLIF(fy25_avg_daily_spend, 0), 0) - 1 AS yoy_change
        FROM
          `{project_id}.{dataset}.fiscal_year_comparison`
        """
        
        # Add filters if provided
        filters = []
        if environment_type:
            filters.append(f"LOWER(environment) = LOWER('{environment_type}')")
        if cto:
            filters.append(f"cto = '{cto}'")
        
        if filters:
            query += " WHERE " + " AND ".join(filters)
        
        # Add order by and limit
        query += f" ORDER BY date DESC, yoy_change DESC LIMIT {limit}"
        
        # Execute query
        df = client.query(query).to_dataframe(create_bqstorage_client=True)
        
        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting fiscal year comparison: {e}")
        return pd.DataFrame()

def get_cost_forecast(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    environment_type: Optional[str] = None,
    cto: Optional[str] = None,
    limit: int = 10
) -> pd.DataFrame:
    """
    Get cost forecast data from the cost_forecast view.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        environment_type: Optional filter for environment column
        cto: Optional filter for cto column
        limit: Maximum number of rows to return
        
    Returns:
        DataFrame with cost forecast data
    """
    try:
        # Build query using the cost_forecast view
        query = f"""
        SELECT
          date,
          environment,
          cto,
          current_spend,
          forecasted_spend,
          total_spend,
          percent_change
        FROM
          `{project_id}.{dataset}.cost_forecast`
        """
        
        # Add filters if provided
        filters = []
        if environment_type:
            filters.append(f"LOWER(environment) = LOWER('{environment_type}')")
        if cto:
            filters.append(f"cto = '{cto}'")
        
        if filters:
            query += " WHERE " + " AND ".join(filters)
        
        # Add order by and limit
        query += f" ORDER BY date DESC, percent_change DESC LIMIT {limit}"
        
        # Execute query
        df = client.query(query).to_dataframe(create_bqstorage_client=True)
        
        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting cost forecast: {e}")
        return pd.DataFrame()