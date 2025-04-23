import pandas as pd
import calendar
from datetime import datetime


def load_data(file_path):
    """Load and preprocess the FinOps data."""
    df = pd.read_csv(file_path)
    
    # Fix column names
    # Check if headers have parentheses and fix them
    for col in df.columns:
        if col.startswith('(') and col.endswith(')'):
            new_col = col[1:-1]  # Remove first and last character
            df.rename(columns={col: new_col}, inplace=True)
    
    # Convert cost to numeric
    df['Cost'] = pd.to_numeric(df['Cost'])
    
    # Convert DATE to datetime if it exists
    if 'DATE' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['DATE']):
            df['DATE'] = pd.to_datetime(df['DATE'])
    
    return df


def get_period_data(df, period_type, period_value, year, parent_grouping, parent_grouping_value=None):
    """Filter data for specified period and organization."""
    # Filter based on period type
    if period_type == 'month':
        filtered_df = df[(df['Month'] == period_value) & (df['FY'] == int(year))]
    elif period_type == 'quarter':
        filtered_df = df[(df['QTR'] == period_value) & (df['FY'] == int(year))]
    elif period_type == 'week':
        # Week in format 'Week XX'
        week_str = f"Week {int(period_value):02d}"
        filtered_df = df[(df['WM_WEEK'] == week_str) & (df['FY'] == int(year))]
    elif period_type == 'year':
        filtered_df = df[df['FY'] == int(period_value)]
    else:
        raise ValueError(f"Invalid period_type: {period_type}")
    
    # Filter by parent grouping if specified
    if parent_grouping_value:
        filtered_df = filtered_df[filtered_df[parent_grouping] == parent_grouping_value]
    
    return filtered_df


def get_previous_period(period_type, period_value, year):
    """Get the previous period based on period type."""
    if period_type == 'month':
        # Get previous month
        month_num = list(calendar.month_abbr).index(period_value)
        prev_month_num = (month_num - 1) if month_num > 1 else 12
        prev_year = int(year) if month_num > 1 else int(year) - 1
        prev_period = calendar.month_abbr[prev_month_num]
        return prev_period, str(prev_year)
    
    elif period_type == 'quarter':
        # Get previous quarter
        quarter_num = int(period_value[1])
        prev_quarter_num = (quarter_num - 1) if quarter_num > 1 else 4
        prev_year = int(year) if quarter_num > 1 else int(year) - 1
        prev_period = f"Q{prev_quarter_num}"
        return prev_period, str(prev_year)
    
    elif period_type == 'week':
        # Get previous week
        week_num = int(period_value)
        if week_num > 1:
            prev_period = str(week_num - 1)
            prev_year = year
        else:
            # Last week of previous year (approximately 52, but can be 53)
            # For simplicity, we assume 52 weeks
            prev_period = "52"
            prev_year = str(int(year) - 1)
        return prev_period, prev_year
    
    elif period_type == 'year':
        # Get previous year
        prev_period = str(int(period_value) - 1)
        return prev_period, None
    
    else:
        raise ValueError(f"Invalid period_type: {period_type}")


def get_period_display_name(period_type, period_value, year=None):
    """Get a human-readable display name for the period."""
    if period_type == 'month':
        return f"{period_value} {year}" if year else period_value
    elif period_type == 'quarter':
        return f"{period_value} {year}" if year else period_value
    elif period_type == 'week':
        return f"Week {period_value}, {year}" if year else f"Week {period_value}"
    elif period_type == 'year':
        return f"FY{period_value}"
    else:
        return str(period_value)


def aggregate_by_application(df, grouping_col="Application_Name"):
    """Aggregate costs by application name or other grouping column."""
    if df.empty:
        return pd.DataFrame(columns=[grouping_col, 'Total_Cost'])
    
    agg_df = df.groupby(grouping_col)['Cost'].sum().reset_index()
    agg_df.rename(columns={'Cost': 'Total_Cost'}, inplace=True)
    return agg_df


def analyze_cost_changes(current_df, previous_df, grouping_col="Application_Name", top_n=10):
    """Analyze cost changes between current and previous periods."""
    if current_df.empty and previous_df.empty:
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
    
    # Handle case where one period has data but other doesn't
    if current_df.empty:
        total_previous = previous_df['Cost'].sum()
        return {
            'total_previous': total_previous,
            'total_current': 0,
            'net_change': -total_previous,
            'percent_change': -100.0,
            'investments': 0,
            'efficiencies': -total_previous,
            'top_investments': pd.DataFrame(),
            'top_efficiencies': pd.DataFrame(columns=[grouping_col, 'Total_Cost_current', 'Total_Cost_previous', 'Change', 'Percent_Change'])
        }
    
    if previous_df.empty:
        total_current = current_df['Cost'].sum()
        return {
            'total_previous': 0,
            'total_current': total_current,
            'net_change': total_current,
            'percent_change': 100.0,
            'investments': total_current,
            'efficiencies': 0,
            'top_investments': pd.DataFrame(columns=[grouping_col, 'Total_Cost_current', 'Total_Cost_previous', 'Change', 'Percent_Change']),
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


def get_env_distribution(df, envs=None):
    """Calculate distribution of costs by environment (Prod vs. non-Prod)."""
    if df.empty:
        return {
            'total_cost': 0,
            'prod_cost': 0,
            'nonprod_cost': 0,
            'prod_percentage': 0,
            'nonprod_percentage': 0,
            'env_breakdown': pd.DataFrame()
        }
    
    # Default environment mapping if not provided
    if envs is None:
        prod_envs = ['Prod']
        nonprod_envs = ['Dev', 'Stage', 'Test', 'QA']
    else:
        prod_envs = envs.get('prod', ['Prod'])
        nonprod_envs = envs.get('nonprod', ['Dev', 'Stage', 'Test', 'QA'])
    
    # Calculate costs by environment type
    total_cost = df['Cost'].sum()
    prod_cost = df[df['Env'].isin(prod_envs)]['Cost'].sum()
    nonprod_cost = df[df['Env'].isin(nonprod_envs)]['Cost'].sum()
    
    # Calculate percentages
    prod_percentage = (prod_cost / total_cost * 100) if total_cost > 0 else 0
    nonprod_percentage = (nonprod_cost / total_cost * 100) if total_cost > 0 else 0
    
    # Get detailed breakdown by environment
    env_breakdown = df.groupby('Env')['Cost'].sum().reset_index()
    env_breakdown.columns = ['Environment', 'Cost']
    env_breakdown['Percentage'] = env_breakdown['Cost'] / total_cost * 100
    env_breakdown['Type'] = 'Other'
    env_breakdown.loc[env_breakdown['Environment'].isin(prod_envs), 'Type'] = 'Production'
    env_breakdown.loc[env_breakdown['Environment'].isin(nonprod_envs), 'Type'] = 'Non-Production'
    
    return {
        'total_cost': total_cost,
        'prod_cost': prod_cost,
        'nonprod_cost': nonprod_cost,
        'prod_percentage': prod_percentage,
        'nonprod_percentage': nonprod_percentage,
        'env_breakdown': env_breakdown
    }


def analyze_env_by_grouping(df, grouping_col, top_n=10, nonprod_threshold=20):
    """Analyze environment distribution (Prod vs. Non-Prod) by grouping column."""
    if df.empty:
        return {
            'total_records': 0,
            'group_env_data': pd.DataFrame(),
            'high_nonprod_groups': pd.DataFrame()
        }
    
    # Aggregate by grouping column and environment
    group_env_data = df.groupby([grouping_col, 'Env']).agg({'Cost': 'sum'}).reset_index()
    
    # Calculate totals by grouping
    group_totals = df.groupby(grouping_col).agg({'Cost': 'sum'}).reset_index()
    group_totals.rename(columns={'Cost': 'Total_Cost'}, inplace=True)
    
    # Merge to get percentages
    merged_data = group_env_data.merge(group_totals, on=grouping_col)
    merged_data['Percentage'] = merged_data['Cost'] / merged_data['Total_Cost'] * 100
    
    # Identify Production vs Non-Production
    merged_data['Env_Type'] = 'Other'
    merged_data.loc[merged_data['Env'] == 'Prod', 'Env_Type'] = 'Production'
    merged_data.loc[merged_data['Env'].isin(['Dev', 'Stage', 'Test', 'QA']), 'Env_Type'] = 'Non-Production'
    
    # Create a pivot table to get Prod vs Non-Prod by group
    pivoted = merged_data.pivot_table(
        index=grouping_col,
        columns='Env_Type',
        values='Percentage',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Ensure all columns exist
    for col in ['Production', 'Non-Production', 'Other']:
        if col not in pivoted.columns:
            pivoted[col] = 0
    
    # Add Total_Cost column
    pivoted = pivoted.merge(group_totals, on=grouping_col)
    
    # Identify groups with high non-production percentage
    high_nonprod = pivoted[pivoted['Non-Production'] >= nonprod_threshold].sort_values(
        by='Non-Production', ascending=False
    ).head(top_n)
    
    return {
        'total_records': len(pivoted),
        'group_env_data': pivoted,
        'high_nonprod_groups': high_nonprod
    }