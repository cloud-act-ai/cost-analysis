"""
BigQuery utilities for FinOps360 cost analysis.
"""
import os
import logging
import pandas as pd
from google.cloud import bigquery
from typing import Optional, List, Dict, Any, Union

logger = logging.getLogger(__name__)

def load_sql_query(query_name: str, **kwargs) -> str:
    """
    Load a SQL query from file and format it with parameters.
    
    Args:
        query_name: Name of the SQL file (without extension)
        **kwargs: Parameters to format the query with
        
    Returns:
        Formatted SQL query string
    """
    # Determine the base path of the application
    base_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "../.."))
    sql_dir = os.path.join(base_dir, "app", "sql")
    
    # Full path to the SQL file
    sql_file = os.path.join(sql_dir, f"{query_name}.sql")
    
    try:
        # Log query loading
        logger.info(f"Loading SQL query: {query_name}")
        
        # Log parameters
        if kwargs:
            logger.info(f"Query parameters:")
            for key, value in kwargs.items():
                logger.info(f"  {key}: {value}")
        
        with open(sql_file, 'r') as f:
            query = f.read()
        
        # Format the query with the provided parameters
        if kwargs:
            query = query.format(**kwargs)
            
        return query
    except Exception as e:
        logger.error(f"Error loading SQL query {query_name}: {e}")
        return ""

def setup_bigquery_client(project_id: str, credentials_path: Optional[str] = None) -> bigquery.Client:
    """
    Set up a BigQuery client.
    
    Args:
        project_id: Google Cloud project ID
        credentials_path: Path to credentials JSON file (optional)
        
    Returns:
        BigQuery client
    """
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    return bigquery.Client(project=project_id)

def run_query(client: bigquery.Client, query: str) -> pd.DataFrame:
    """
    Run a BigQuery query and return results as a DataFrame.
    
    Args:
        client: BigQuery client
        query: SQL query to execute
        
    Returns:
        DataFrame with query results
    """
    # Check if client is a mock (sample data mode)
    if hasattr(client, "__class__") and client.__class__.__name__ == "MagicMock":
        logger.warning("Using mock BigQuery client - returning empty DataFrame to trigger sample data")
        return pd.DataFrame()
        
    try:
        # Log the query for debugging purposes
        logger.info(f"Executing query: \n{query}\n")
        
        # Execute the query
        job = client.query(query)
        
        # Log query execution details
        logger.info(f"Query job ID: {job.job_id}")
        logger.info(f"Query state: {job.state}")
        
        # Convert to dataframe with error handling for db-dtypes
        try:
            # Try with optimized storage client
            df = job.to_dataframe(create_bqstorage_client=True)
        except ImportError as e:
            if "db-dtypes" in str(e):
                logger.warning("db-dtypes package not found. Using standard conversion method.")
                # Fall back to standard conversion without BigQuery Storage API
                df = job.to_dataframe(create_bqstorage_client=False)
            else:
                # Re-raise other import errors
                raise
        
        # Log result summary
        logger.info(f"Query returned {len(df)} rows")
        if not df.empty:
            logger.info(f"Columns: {df.columns.tolist()}")
        
        return df
    except Exception as e:
        logger.error(f"Error running query: {e}")
        logger.error(f"Query: {query}")
        return pd.DataFrame()