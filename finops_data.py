import pandas as pd
import calendar
from datetime import datetime


def load_data(file_path):
    """Load and preprocess the FinOps data."""
    df = pd.read_csv(file_path)
    
    # Convert cost to numeric
    df['Cost'] = pd.to_numeric(df['Cost'])
    
    # Convert DATE to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df['DATE']):
        df['DATE'] = pd.to_datetime(df['DATE'])
    
    return df


def get_month_data(df, month, year, parent_grouping, parent_grouping_value=None):
    """Filter data for specified month and organization."""
    # Filter for the specified month and year
    filtered_df = df[(df['Month'] == month) & (df['FY'] == int(year))]
    
    # Filter by parent grouping if specified
    if parent_grouping_value:
        filtered_df = filtered_df[filtered_df[parent_grouping] == parent_grouping_value]
    
    return filtered_df


def get_previous_month(month, year):
    """Get the previous month name and year."""
    month_num = list(calendar.month_abbr).index(month)
    prev_month_num = (month_num - 1) if month_num > 1 else 12
    prev_year = int(year) if month_num > 1 else int(year) - 1
    prev_month = calendar.month_abbr[prev_month_num]
    
    return prev_month, str(prev_year)


def aggregate_by_application(df, grouping_col="Application_Name"):
    """Aggregate costs by application name or other grouping column."""
    if df.empty:
        return pd.DataFrame(columns=[grouping_col, 'Total_Cost'])
    
    agg_df = df.groupby(grouping_col)['Cost'].sum().reset_index()
    agg_df.rename(columns={'Cost': 'Total_Cost'}, inplace=True)
    return agg_df


def analyze_cost_changes(current_df, previous_df, grouping_col="Application_Name", top_n=10):
    """Analyze cost changes between current and previous month."""
    if current_df.empty or previous_df.empty:
        return {
            'total_previous': 0,
            'total_current': 0,
            'net_change': 0,
            'percent_change': 0,
            'investments': 0,
            'efficiencies': 0,
            'top_investments': pd.DataFrame(),
            'top_efficiencies': pd.DataFrame()
        }
    
    # Aggregate by application
    current_agg = aggregate_by_application(current_df, grouping_col)
    previous_agg = aggregate_by_application(previous_df, grouping_col)
    
    # Merge current and previous data
    merged_df = current_agg.merge(
        previous_agg, 
        on=grouping_col, 
        how='outer', 
        suffixes=('_current', '_previous')
    ).fillna(0)
    
    # Calculate changes
    merged_df['Change'] = merged_df['Total_Cost_current'] - merged_df['Total_Cost_previous']
    merged_df['Percent_Change'] = 0.0
    
    # Avoid division by zero
    mask = merged_df['Total_Cost_previous'] > 0
    merged_df.loc[mask, 'Percent_Change'] = (
        merged_df.loc[mask, 'Change'] / merged_df.loc[mask, 'Total_Cost_previous'] * 100
    )
    
    # Identify investments (cost increases) and efficiencies (cost decreases)
    investments_df = merged_df[merged_df['Change'] > 0].sort_values(by='Change', ascending=False)
    efficiencies_df = merged_df[merged_df['Change'] < 0].sort_values(by='Change', ascending=True)
    
    # Get top N for each category
    top_investments = investments_df.head(top_n)
    top_efficiencies = efficiencies_df.head(top_n)
    
    # Calculate totals
    total_previous = previous_agg['Total_Cost'].sum()
    total_current = current_agg['Total_Cost'].sum()
    net_change = total_current - total_previous
    percent_change = (net_change / total_previous * 100) if total_previous > 0 else 0
    total_investments = investments_df['Change'].sum()
    total_efficiencies = efficiencies_df['Change'].sum()
    
    return {
        'total_previous': total_previous,
        'total_current': total_current,
        'net_change': net_change,
        'percent_change': percent_change,
        'investments': total_investments,
        'efficiencies': total_efficiencies,
        'top_investments': top_investments,
        'top_efficiencies': top_efficiencies
    }