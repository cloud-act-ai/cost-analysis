import pandas as pd
import pandas_gbq
from google.cloud import bigquery
import os
from datetime import datetime

def load_data_from_bigquery(project_id, dataset, table, credentials_path=None):
    """
    Load FinOps data from a BigQuery table.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        credentials_path: Optional path to service account credentials JSON file
    
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
                                  filter_column=None, filter_value=None, credentials_path=None):
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
        full_df = load_data_from_bigquery(project_id, dataset, table, credentials_path)
        
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
    
    # Create the query
    query = f"""
    SELECT * 
    FROM `{project_id}.{dataset}.{table}`
    WHERE {where_clause}
    """
    
    try:
        # Execute the query
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