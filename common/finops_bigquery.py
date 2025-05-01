import pandas as pd
import pandas_gbq
from google.cloud import bigquery
import os
from datetime import datetime
from google.cloud.bigquery import Client, QueryJobConfig
from google.cloud.bigquery_storage import BigQueryReadClient

def load_data_from_bigquery(project_id, dataset, table, credentials_path=None, use_bqdf=True):
    """
    Load FinOps data from a BigQuery table.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        credentials_path: Optional path to service account credentials JSON file
        use_bqdf: Use BigQuery DataFrames for better performance with large datasets
    
    Returns:
        DataFrame with the FinOps data
    """
    # Set credentials if provided
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    # Create the query to fetch all data from the table
    query = f"""
    SELECT * 
    FROM `{project_id}.{dataset}.{table}`
    """
    
    try:
        if use_bqdf:
            # Initialize BigQuery client for optimal performance
            bq_client = Client(project=project_id)
            
            # Create reference to BigQuery table
            table_ref = f"{project_id}.{dataset}.{table}"
            
            # Use the bigquery_storage_client parameter to enable faster downloads
            df = bq_client.list_rows(table_ref).to_dataframe(
                create_bqstorage_client=True
            )
        else:
            # Use pandas_gbq to execute the query and load into a DataFrame
            df = pandas_gbq.read_gbq(query, project_id=project_id)
        
        # Fix column names
        # Check if headers have parentheses and fix them
        for col in df.columns:
            if col.startswith('(') and col.endswith(')'):
                new_col = col[1:-1]  # Remove first and last character
                df.rename(columns={col: new_col}, inplace=True)
        
        # Convert cost to numeric - handle both old and new schema
        cost_column = 'Cost' if 'Cost' in df.columns else 'cost'
        df[cost_column] = pd.to_numeric(df[cost_column])
        
        # Convert date to datetime if it exists
        date_column = 'DATE' if 'DATE' in df.columns else 'date'
        if date_column in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                df[date_column] = pd.to_datetime(df[date_column])
        
        # Ensure required fields are available for the environment analyzer
        # Map new schema columns to old schema columns if needed
        if 'environment' in df.columns and 'Env' not in df.columns:
            df['Env'] = df['environment']
        
        if 'Cost' not in df.columns and 'cost' in df.columns:
            df['Cost'] = df['cost']
        
        # Handle organizational structure columns
        if 'tr_product_pillar_team' in df.columns and 'PILLAR' not in df.columns:
            df['PILLAR'] = df['tr_product_pillar_team']
        
        if 'vp' in df.columns and 'VP' not in df.columns:
            df['VP'] = df['vp']
        
        if 'application' in df.columns:
            if 'ORG' not in df.columns:
                df['ORG'] = df['application']
            if 'Application_Name' not in df.columns:
                df['Application_Name'] = df['application']
        
        return df
    
    except Exception as e:
        print(f"Error loading data from BigQuery: {e}")
        raise

def load_period_data_from_bigquery(project_id, dataset, table, period_type, period_value, year, 
                                  filter_column=None, filter_value=None, credentials_path=None, use_bqdf=True):
    """
    Load FinOps data for a specific period from BigQuery.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        period_type: Type of period ('month', 'quarter', 'week', 'year')
        period_value: Value for the period (e.g., 'Mar', 'Q1')
        year: Year to filter by (e.g., 'FY2024')
        filter_column: Optional column to filter by (e.g., 'cto')
        filter_value: Value for the filter column
        credentials_path: Optional path to service account credentials JSON file
        use_bqdf: Use BigQuery DataFrames for better performance with large datasets
    
    Returns:
        DataFrame with the filtered FinOps data
    """
    # Set credentials if provided
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    # Map period_type to corresponding column names
    period_columns = {
        'month': 'Month',
        'quarter': 'qtr',
        'week': 'week',
        'year': 'fy'
    }
    
    # Handle special cases for 'last' and 'current'
    if period_value == 'last' or year == 'current':
        # Load full data to determine last period or current year
        full_df = load_data_from_bigquery(project_id, dataset, table, credentials_path, use_bqdf)
        
        # Use existing functions to determine actual values
        from common.finops_data import get_last_period, get_current_fiscal_year
        
        if period_value == 'last':
            actual_period_value, period_year = get_last_period(full_df, period_type)
            if period_year is not None:
                year = period_year
        
        if year == 'current':
            year = get_current_fiscal_year(full_df)
        
        # After determining values, we can filter using BigQuery for efficiency
        period_value = actual_period_value
    
    # Build the appropriate WHERE clauses for BigQuery
    where_clauses = []
    
    # Add period filter
    period_col = period_columns.get(period_type)
    if period_col and period_value:
        # Special handling for different period formats
        if period_type == 'month':
            where_clauses.append(f"Month = '{period_value}'")
        elif period_type == 'quarter':
            # Handle 'Q1' format
            if isinstance(period_value, str) and period_value.startswith('Q'):
                try:
                    qtr_num = int(period_value[1])
                    where_clauses.append(f"qtr = {qtr_num}")
                except (ValueError, IndexError):
                    where_clauses.append(f"qtr = '{period_value}'")
            else:
                where_clauses.append(f"qtr = {period_value}")
        elif period_type == 'week':
            # Handle 'Week XX' format
            if isinstance(period_value, str) and period_value.startswith('Week'):
                try:
                    week_num = int(''.join(filter(str.isdigit, period_value)))
                    where_clauses.append(f"week = {week_num}")
                except ValueError:
                    where_clauses.append(f"week = '{period_value}'")
            else:
                where_clauses.append(f"week = {period_value}")
        elif period_type == 'year':
            # Handle fiscal year format
            if isinstance(period_value, str) and period_value.startswith('FY'):
                where_clauses.append(f"fy = '{period_value}'")
            else:
                where_clauses.append(f"fy = '{year}'")
    
    # Add year filter if not already included and not for year period_type
    if year and period_type != 'year':
        # Check if year is fiscal year format
        if isinstance(year, str) and year.startswith('FY'):
            where_clauses.append(f"fy = '{year}'")
        else:
            where_clauses.append(f"fy = '{year}'")
    
    # Add additional filter if specified
    if filter_column and filter_value:
        where_clauses.append(f"{filter_column} = '{filter_value}'")
    
    # Combine WHERE clauses
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    try:
        if use_bqdf:
            # Initialize BigQuery client
            bq_client = Client(project=project_id)
            
            # Create the query with filter applied directly
            table_id = f"{project_id}.{dataset}.{table}"
            query = f"""
            SELECT * 
            FROM `{table_id}`
            WHERE {where_clause}
            """
            
            # Configure the query job
            job_config = QueryJobConfig(use_query_cache=True)
            
            # Run the query and create a DataFrame with BigQuery Storage API
            query_job = bq_client.query(query, job_config=job_config)
            df = query_job.to_dataframe(create_bqstorage_client=True)
        else:
            # Create the query
            query = f"""
            SELECT * 
            FROM `{project_id}.{dataset}.{table}`
            WHERE {where_clause}
            """
            
            # Execute the query with pandas_gbq
            df = pandas_gbq.read_gbq(query, project_id=project_id)
        
        # Apply the same data normalization as in load_data_from_bigquery
        # Convert cost to numeric
        cost_column = 'Cost' if 'Cost' in df.columns else 'cost'
        df[cost_column] = pd.to_numeric(df[cost_column])
        
        # Map columns for compatibility
        if 'environment' in df.columns and 'Env' not in df.columns:
            df['Env'] = df['environment']
        
        if 'Cost' not in df.columns and 'cost' in df.columns:
            df['Cost'] = df['cost']
        
        if 'tr_product_pillar_team' in df.columns and 'PILLAR' not in df.columns:
            df['PILLAR'] = df['tr_product_pillar_team']
        
        if 'vp' in df.columns and 'VP' not in df.columns:
            df['VP'] = df['vp']
        
        if 'application' in df.columns:
            if 'ORG' not in df.columns:
                df['ORG'] = df['application']
            if 'Application_Name' not in df.columns:
                df['Application_Name'] = df['application']
        
        return df
    
    except Exception as e:
        print(f"Error loading period data from BigQuery: {e}")
        raise

def filter_bigquery_data(project_id, dataset, table, filters=None, columns=None, credentials_path=None):
    """
    Advanced filtering of BigQuery data using BigQuery DataFrames.
    This function offloads filtering to BigQuery's servers before returning results,
    significantly reducing data transfer and memory usage for large datasets.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        filters: Dictionary of filter conditions {column: value} or {column: [operator, value]}
                 Supported operators: '=', '!=', '>', '<', '>=', '<=', 'IN', 'NOT IN', 'LIKE'
        columns: List of columns to fetch (None for all columns)
        credentials_path: Optional path to service account credentials JSON file
    
    Returns:
        DataFrame with the filtered data
    """
    # Set credentials if provided
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    try:
        # Initialize BigQuery client
        bq_client = Client(project=project_id)
        
        # Build column selection
        column_selection = "*"
        if columns:
            column_selection = ", ".join(columns)
        
        # Build WHERE clause for filters
        where_clauses = []
        if filters:
            for column, condition in filters.items():
                if isinstance(condition, list):
                    operator, value = condition
                    # Handle special operators
                    if operator.upper() in ['IN', 'NOT IN']:
                        if isinstance(value, list):
                            formatted_values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in value])
                            where_clauses.append(f"{column} {operator} ({formatted_values})")
                        else:
                            raise ValueError(f"Value for IN/NOT IN operator must be a list: {value}")
                    elif operator.upper() == 'LIKE':
                        where_clauses.append(f"{column} LIKE '{value}'")
                    else:
                        # For standard comparison operators
                        if isinstance(value, str):
                            where_clauses.append(f"{column} {operator} '{value}'")
                        else:
                            where_clauses.append(f"{column} {operator} {value}")
                else:
                    # Default to equality
                    if isinstance(condition, str):
                        where_clauses.append(f"{column} = '{condition}'")
                    else:
                        where_clauses.append(f"{column} = {condition}")
        
        # Create the query
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        query = f"""
        SELECT {column_selection}
        FROM `{project_id}.{dataset}.{table}`
        WHERE {where_clause}
        """
        
        # Configure the query job with caching
        job_config = QueryJobConfig(use_query_cache=True)
        
        # Run the query and create a BigQueryDataFrame
        query_job = bq_client.query(query, job_config=job_config)
        bqdf = BigQueryDataFrame(
            source_or_reference=query_job,
            client=bq_client,
            storage_client=storage_client
        )
        
        # Convert to pandas DataFrame for compatibility with the rest of the codebase
        df = bqdf.to_pandas()
        
        # Apply the standard column normalization as in other functions
        # Fix column names
        for col in df.columns:
            if col.startswith('(') and col.endswith(')'):
                new_col = col[1:-1]  # Remove first and last character
                df.rename(columns={col: new_col}, inplace=True)
        
        # Convert cost to numeric - handle both old and new schema
        cost_column = 'Cost' if 'Cost' in df.columns else 'cost'
        if cost_column in df.columns:
            df[cost_column] = pd.to_numeric(df[cost_column])
        
        # Map columns for compatibility
        if 'environment' in df.columns and 'Env' not in df.columns:
            df['Env'] = df['environment']
        
        if 'Cost' not in df.columns and 'cost' in df.columns:
            df['Cost'] = df['cost']
        
        if 'tr_product_pillar_team' in df.columns and 'PILLAR' not in df.columns:
            df['PILLAR'] = df['tr_product_pillar_team']
        
        if 'vp' in df.columns and 'VP' not in df.columns:
            df['VP'] = df['vp']
        
        if 'application' in df.columns:
            if 'ORG' not in df.columns:
                df['ORG'] = df['application']
            if 'Application_Name' not in df.columns:
                df['Application_Name'] = df['application']
        
        return df
        
    except Exception as e:
        print(f"Error filtering data from BigQuery: {e}")
        raise

def aggregate_bigquery_data(project_id, dataset, table, group_by, agg_functions, filters=None, 
                           having=None, order_by=None, limit=None, credentials_path=None):
    """
    Perform efficient data aggregation directly in BigQuery using SQL.
    This function pushes aggregation operations to BigQuery instead of loading data locally first.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        group_by: List of columns to group by
        agg_functions: Dictionary mapping column names to aggregation functions
                      e.g. {'Cost': 'SUM', 'instances': 'COUNT'}
        filters: Dictionary of filter conditions (same format as filter_bigquery_data)
        having: Dictionary of having conditions for filtering after aggregation
        order_by: Dictionary of columns and direction for ordering {'column': 'ASC'/'DESC'}
        limit: Maximum number of rows to return (None for all rows)
        credentials_path: Optional path to service account credentials JSON file
    
    Returns:
        DataFrame with the aggregated data
    """
    # Set credentials if provided
    if credentials_path:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    
    try:
        # Initialize BigQuery client
        bq_client = Client(project=project_id)
        
        # Build SELECT with aggregation functions
        select_clauses = []
        
        # Add GROUP BY columns to select
        for col in group_by:
            select_clauses.append(col)
        
        # Add aggregation functions
        for col, agg_func in agg_functions.items():
            select_clauses.append(f"{agg_func}({col}) AS {col}_{agg_func.lower()}")
        
        select_clause = ", ".join(select_clauses)
        
        # Build WHERE clause for filters
        where_clauses = []
        if filters:
            for column, condition in filters.items():
                if isinstance(condition, list):
                    operator, value = condition
                    # Handle special operators (same as in filter_bigquery_data)
                    if operator.upper() in ['IN', 'NOT IN']:
                        if isinstance(value, list):
                            formatted_values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in value])
                            where_clauses.append(f"{column} {operator} ({formatted_values})")
                        else:
                            raise ValueError(f"Value for IN/NOT IN operator must be a list: {value}")
                    elif operator.upper() == 'LIKE':
                        where_clauses.append(f"{column} LIKE '{value}'")
                    else:
                        # For standard comparison operators
                        if isinstance(value, str):
                            where_clauses.append(f"{column} {operator} '{value}'")
                        else:
                            where_clauses.append(f"{column} {operator} {value}")
                else:
                    # Default to equality
                    if isinstance(condition, str):
                        where_clauses.append(f"{column} = '{condition}'")
                    else:
                        where_clauses.append(f"{column} = {condition}")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Build GROUP BY clause
        group_by_clause = ", ".join(group_by)
        
        # Build HAVING clause
        having_clauses = []
        if having:
            for column, condition in having.items():
                if isinstance(condition, list):
                    operator, value = condition
                    # Similar handling as WHERE clauses
                    if isinstance(value, str):
                        having_clauses.append(f"{column} {operator} '{value}'")
                    else:
                        having_clauses.append(f"{column} {operator} {value}")
                else:
                    # Default to equality
                    if isinstance(condition, str):
                        having_clauses.append(f"{column} = '{condition}'")
                    else:
                        having_clauses.append(f"{column} = {condition}")
        
        having_clause = " AND ".join(having_clauses) if having_clauses else ""
        
        # Build ORDER BY clause
        order_clauses = []
        if order_by:
            for column, direction in order_by.items():
                order_clauses.append(f"{column} {direction}")
        
        order_clause = ", ".join(order_clauses) if order_clauses else ""
        
        # Build the complete query
        query = f"""
        SELECT {select_clause}
        FROM `{project_id}.{dataset}.{table}`
        WHERE {where_clause}
        GROUP BY {group_by_clause}
        """
        
        if having_clause:
            query += f" HAVING {having_clause}"
        
        if order_clause:
            query += f" ORDER BY {order_clause}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        # Configure the query job with caching
        job_config = QueryJobConfig(use_query_cache=True)
        
        # Run the query and create a DataFrame with BigQuery Storage API
        query_job = bq_client.query(query, job_config=job_config)
        df = query_job.to_dataframe(create_bqstorage_client=True)
        
        return df
        
    except Exception as e:
        print(f"Error aggregating data from BigQuery: {e}")
        raise