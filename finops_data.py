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