"""
BigQuery utilities for FinOps360 cost analysis.
"""
import os
import logging
import pandas as pd
from google.cloud import bigquery
from typing import Optional, List, Dict, Any, Union

logger = logging.getLogger(__name__)

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
    try:
        return client.query(query).to_dataframe(create_bqstorage_client=True)
    except Exception as e:
        logger.error(f"Error running query: {e}")
        logger.error(f"Query: {query}")
        return pd.DataFrame()