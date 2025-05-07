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


def get_last_period(df, period_type):
    """Determine the most recent period in the dataset."""
    # Identify the appropriate columns based on schema
    date_col = 'DATE' if 'DATE' in df.columns else 'date'
    month_col = 'Month' if 'Month' in df.columns else 'month'
    qtr_col = 'QTR' if 'QTR' in df.columns else 'qtr'
    week_col = 'WM_WEEK' if 'WM_WEEK' in df.columns else 'week'
    fy_col = 'FY' if 'FY' in df.columns else 'fy'
    
    # Ensure date column is datetime type
    if date_col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])
    
    # Get the most recent date
    if date_col in df.columns:
        last_date = df[date_col].max()
        
        if period_type == 'month':
            # Get month name of last date
            if month_col == 'Month':
                # Use existing Month column
                last_date_str = pd.to_datetime(last_date).strftime('%b')
                # Convert to title case to match Month format (Jan, Feb, etc.)
                last_period = last_date_str.title()
            else:
                # For numerical month, just get the month number
                last_period = pd.to_datetime(last_date).month
            
            # Also get the fiscal year
            if fy_col in df.columns:
                # Get unique FY value for this month
                month_df = df[df[month_col] == last_period]
                if not month_df.empty:
                    last_year = month_df[fy_col].iloc[0]
                else:
                    # Default to most common FY value
                    last_year = df[fy_col].value_counts().index[0]
            else:
                # Default to calendar year
                last_year = pd.to_datetime(last_date).year
                
        elif period_type == 'quarter':
            # Get quarter of last date
            quarter = (pd.to_datetime(last_date).month - 1) // 3 + 1
            if qtr_col == 'QTR':
                last_period = f"Q{quarter}"
            else:
                last_period = quarter
            
            # Get fiscal year
            if fy_col in df.columns:
                quarter_df = df[df[qtr_col] == last_period]
                if not quarter_df.empty:
                    last_year = quarter_df[fy_col].iloc[0]
                else:
                    last_year = df[fy_col].value_counts().index[0]
            else:
                last_year = pd.to_datetime(last_date).year
                
        elif period_type == 'week':
            # Get week number of last date
            week_num = pd.to_datetime(last_date).isocalendar()[1]
            if week_col == 'WM_WEEK':
                last_period = f"Week {week_num:02d}"
            else:
                last_period = week_num
            
            # Get fiscal year
            if fy_col in df.columns:
                week_df = df[df[week_col] == last_period]
                if not week_df.empty:
                    last_year = week_df[fy_col].iloc[0]
                else:
                    last_year = df[fy_col].value_counts().index[0]
            else:
                last_year = pd.to_datetime(last_date).year
                
        elif period_type == 'year':
            # For yearly analysis, just get the year
            if fy_col in df.columns:
                # Use the most recent fiscal year
                last_period = df[fy_col].max()
                last_year = None  # Year is already in the period value
            else:
                last_period = pd.to_datetime(last_date).year
                last_year = None
    else:
        # If no date column, fall back to using existing period columns
        if period_type == 'month' and month_col in df.columns:
            # For Month, we need to determine which is the latest (tricky without date)
            month_order = {name: idx for idx, name in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}
            month_values = df[month_col].unique()
            # Convert to a sortable format based on our month_order mapping
            month_idx = {m: month_order.get(m, 999) for m in month_values}  # 999 as fallback for unknown formats
            last_period = sorted(month_values, key=lambda m: month_idx[m])[-1]
            
            # Get fiscal year
            if fy_col in df.columns:
                month_df = df[df[month_col] == last_period]
                last_year = month_df[fy_col].iloc[0]
            else:
                # Without a fiscal year, use the current year
                last_year = datetime.datetime.now().year
                
        elif period_type == 'quarter' and qtr_col in df.columns:
            # For quarters, also need ordering logic
            qtr_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
            qtr_values = df[qtr_col].unique()
            qtr_idx = {q: qtr_order.get(q, int(q) if isinstance(q, (int, float)) else 999) for q in qtr_values}
            last_period = sorted(qtr_values, key=lambda q: qtr_idx[q])[-1]
            
            # Get fiscal year
            if fy_col in df.columns:
                qtr_df = df[df[qtr_col] == last_period]
                last_year = qtr_df[fy_col].iloc[0]
            else:
                last_year = datetime.datetime.now().year
                
        elif period_type == 'week' and week_col in df.columns:
            # For weeks, we should be able to order numerically
            if all(isinstance(w, (int, float)) for w in df[week_col].unique()):
                last_period = df[week_col].max()
            else:
                # Handle text format like "Week 01"
                week_values = df[week_col].unique()
                try:
                    # Extract numbers and find max
                    week_nums = [int(''.join(filter(str.isdigit, str(w)))) for w in week_values]
                    max_week = max(week_nums)
                    # Find corresponding original format
                    matches = [w for w in week_values if str(max_week) in str(w)]
                    last_period = matches[0] if matches else f"Week {max_week:02d}"
                except (ValueError, IndexError):
                    # Fallback: just take the last value alphabetically
                    last_period = sorted(week_values)[-1]
            
            # Get fiscal year
            if fy_col in df.columns:
                week_df = df[df[week_col] == last_period]
                last_year = week_df[fy_col].iloc[0]
            else:
                last_year = datetime.datetime.now().year
                
        elif period_type == 'year' and fy_col in df.columns:
            # For years, just find the max fiscal year
            fy_values = df[fy_col].unique()
            # Extract year numbers for comparison
            fy_nums = []
            for fy in fy_values:
                if isinstance(fy, str) and fy.startswith('FY'):
                    try:
                        fy_nums.append((fy, int(fy[2:])))
                    except ValueError:
                        fy_nums.append((fy, 0))  # Invalid format
                else:
                    fy_nums.append((fy, int(fy) if isinstance(fy, (int, float)) else 0))
            
            # Get the max year
            last_period = max(fy_nums, key=lambda x: x[1])[0]
            last_year = None
        else:
            # No appropriate columns found
            raise ValueError(f"Could not determine last {period_type} without date information.")
    
    return str(last_period), str(last_year) if last_year is not None else None


def get_current_fiscal_year(df):
    """Determine the current fiscal year from the dataset or use current calendar year."""
    fy_col = 'FY' if 'FY' in df.columns else 'fy'
    
    if fy_col in df.columns:
        # Extract year values to find the most recent
        fy_values = df[fy_col].unique()
        
        # Handle different formats (FY2024 or 2024)
        fy_nums = []
        for fy in fy_values:
            if isinstance(fy, str) and fy.startswith('FY'):
                try:
                    fy_nums.append((fy, int(fy[2:])))
                except ValueError:
                    continue
            elif isinstance(fy, (int, float)) or (isinstance(fy, str) and fy.isdigit()):
                fy_nums.append((fy, int(fy)))
        
        if fy_nums:
            # Return the latest fiscal year
            return str(max(fy_nums, key=lambda x: x[1])[0])
    
    # Fallback to current calendar year
    return str(datetime.now().year)


def get_period_data(df, period_type, period_value, year, filter_column=None, filter_value=None):
    """Filter data for specified period.
    
    Args:
        df: DataFrame containing the data
        period_type: Type of period ('month', 'quarter', 'week', 'year')
        period_value: Value for the period (can be 'last')
        year: Year to filter by (can be 'current')
        filter_column: Optional column to filter by (e.g., 'cto')
        filter_value: Value for the filter column
    """
    # Handle different column names between old and new schema
    month_col = 'Month' if 'Month' in df.columns else 'month'
    qtr_col = 'QTR' if 'QTR' in df.columns else 'qtr'
    week_col = 'WM_WEEK' if 'WM_WEEK' in df.columns else 'week'
    fy_col = 'FY' if 'FY' in df.columns else 'fy'
    
    # Handle 'last' period value
    actual_period_value = period_value
    actual_year = year
    
    if period_value == 'last':
        actual_period_value, period_year = get_last_period(df, period_type)
        if period_year is not None:
            actual_year = period_year
            
    # Handle 'current' year value
    if year == 'current':
        actual_year = get_current_fiscal_year(df)
    
    # Filter based on period type
    if period_type == 'month':
        if month_col == 'Month':
            # Old schema: Month name like "Jan"
            filtered_df = df[(df[month_col] == actual_period_value) & (df[fy_col] == actual_year)]
        else:
            # New schema: month as number 1-12
            month_to_name = {idx+1: name for idx, name in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}
            
            # Handle both month name and number
            if isinstance(actual_period_value, str) and actual_period_value in month_to_name.values():
                month_num = next((idx for idx, name in month_to_name.items() if name == actual_period_value), None)
                if month_num:
                    filtered_df = df[(df[month_col] == month_num) & (df[fy_col] == actual_year)]
                else:
                    # Fallback to using the Month column if it exists
                    if 'Month' in df.columns:
                        filtered_df = df[(df['Month'] == actual_period_value) & (df[fy_col] == actual_year)]
                    else:
                        raise ValueError(f"Cannot interpret month value: {actual_period_value}")
            else:
                # It's already a month number
                try:
                    month_num = int(actual_period_value)
                    filtered_df = df[(df[month_col] == month_num) & (df[fy_col] == actual_year)]
                except ValueError:
                    raise ValueError(f"Invalid month format: {actual_period_value}")
    
    elif period_type == 'quarter':
        if qtr_col == 'QTR':
            # Old schema: Quarter value like "Q1"
            filtered_df = df[(df[qtr_col] == actual_period_value) & (df[fy_col] == actual_year)]
        else:
            # New schema: qtr as number 1-4
            if isinstance(actual_period_value, str) and actual_period_value.startswith('Q'):
                try:
                    qtr_num = int(actual_period_value[1])
                    filtered_df = df[(df[qtr_col] == qtr_num) & (df[fy_col] == actual_year)]
                except (ValueError, IndexError):
                    raise ValueError(f"Invalid quarter format: {actual_period_value}")
            else:
                # It's already a quarter number
                try:
                    qtr_num = int(actual_period_value)
                    filtered_df = df[(df[qtr_col] == qtr_num) & (df[fy_col] == actual_year)]
                except ValueError:
                    raise ValueError(f"Invalid quarter format: {actual_period_value}")
    
    elif period_type == 'week':
        if week_col == 'WM_WEEK':
            # Old schema: Week in format 'Week XX'
            if isinstance(actual_period_value, str) and actual_period_value.startswith('Week'):
                filtered_df = df[(df[week_col] == actual_period_value) & (df[fy_col] == actual_year)]
            else:
                # Convert to Week format
                try:
                    week_str = f"Week {int(actual_period_value):02d}"
                    filtered_df = df[(df[week_col] == week_str) & (df[fy_col] == actual_year)]
                except ValueError:
                    raise ValueError(f"Invalid week format: {actual_period_value}")
        else:
            # New schema: week as number
            if isinstance(actual_period_value, str) and actual_period_value.startswith('Week'):
                try:
                    week_num = int(''.join(filter(str.isdigit, actual_period_value)))
                    filtered_df = df[(df[week_col] == week_num) & (df[fy_col] == actual_year)]
                except ValueError:
                    raise ValueError(f"Invalid week format: {actual_period_value}")
            else:
                # It's already a week number
                try:
                    week_num = int(actual_period_value)
                    filtered_df = df[(df[week_col] == week_num) & (df[fy_col] == actual_year)]
                except ValueError:
                    raise ValueError(f"Invalid week format: {actual_period_value}")
    
    elif period_type == 'year':
        # Handle both string and integer fiscal years
        if isinstance(df[fy_col].iloc[0], str) and df[fy_col].iloc[0].startswith('FY'):
            # If FY is in format "FY2024"
            if not str(actual_period_value).startswith('FY'):
                fiscal_year = f"FY{actual_period_value}"
            else:
                fiscal_year = actual_period_value
            filtered_df = df[df[fy_col] == fiscal_year]
        else:
            # If FY is numeric
            if str(actual_period_value).startswith('FY'):
                try:
                    year_num = int(actual_period_value[2:])
                    filtered_df = df[df[fy_col] == year_num]
                except (ValueError, IndexError):
                    filtered_df = df[df[fy_col] == actual_period_value]
            else:
                filtered_df = df[df[fy_col] == actual_period_value]
    else:
        raise ValueError(f"Invalid period_type: {period_type}")
    
    # Apply additional filter if specified
    if filter_column and filter_value and not filtered_df.empty:
        if filter_column in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[filter_column] == filter_value]
    
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


def aggregate_by_application(df, grouping_col="tr_product"):
    """Aggregate costs by product name or other grouping column."""
    if df.empty:
        return pd.DataFrame(columns=[grouping_col, 'Total_Cost'])
    
    # Use cost column or fall back to Cost (for compatibility)
    cost_col = 'cost' if 'cost' in df.columns else 'Cost'
    
    # If the grouping column doesn't exist, use a reasonable default
    if grouping_col not in df.columns:
        for col in ['tr_product', 'managed_service', 'environment']:
            if col in df.columns:
                grouping_col = col
                break
    
    agg_df = df.groupby(grouping_col)[cost_col].sum().reset_index()
    agg_df.rename(columns={cost_col: 'Total_Cost'}, inplace=True)
    return agg_df


def analyze_cost_changes(current_df, previous_df, grouping_col="tr_product", top_n=10):
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
        # For the new schema, adapt to expected environment values
        prod_envs = ['Prod', 'p', 'production', 'prd']
        nonprod_envs = ['Dev', 'Stage', 'Test', 'QA', 'np', 'n', 'nonprod', 'non-prod']
    else:
        prod_envs = envs.get('prod', ['Prod', 'p', 'production', 'prd'])
        nonprod_envs = envs.get('nonprod', ['Dev', 'Stage', 'Test', 'QA', 'np', 'n', 'nonprod', 'non-prod'])
    
    # Use 'Env' for backward compatibility, or 'environment' for new schema
    env_column = 'Env' if 'Env' in df.columns else 'environment'
    cost_column = 'Cost' if 'Cost' in df.columns else 'cost'
    
    # Calculate costs by environment type
    total_cost = df[cost_column].sum()
    prod_cost = df[df[env_column].isin(prod_envs)][cost_column].sum()
    nonprod_cost = df[df[env_column].isin(nonprod_envs)][cost_column].sum()
    
    # Calculate percentages
    prod_percentage = (prod_cost / total_cost * 100) if total_cost > 0 else 0
    nonprod_percentage = (nonprod_cost / total_cost * 100) if total_cost > 0 else 0
    
    # Get detailed breakdown by environment
    env_breakdown = df.groupby(env_column)[cost_column].sum().reset_index()
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
    
    # Use 'Env' for backward compatibility, or 'environment' for new schema
    env_column = 'Env' if 'Env' in df.columns else 'environment'
    cost_column = 'Cost' if 'Cost' in df.columns else 'cost'
    
    # Check if grouping column exists in the dataframe
    if grouping_col not in df.columns:
        # Try to map columns between schemas
        column_mapping = {
            'ORG': 'managed_service',
            'VP': 'cto',
            'PILLAR': 'tr_product_pillar_team',
            'Application_Name': 'tr_product',
            'CTO': 'cto'
        }
        if grouping_col in column_mapping and column_mapping[grouping_col] in df.columns:
            # Create a copy of the grouping column with the old name
            df[grouping_col] = df[column_mapping[grouping_col]]
    
    # Aggregate by grouping column and environment
    group_env_data = df.groupby([grouping_col, env_column]).agg({cost_column: 'sum'}).reset_index()
    
    # Calculate totals by grouping
    group_totals = df.groupby(grouping_col).agg({cost_column: 'sum'}).reset_index()
    group_totals.rename(columns={cost_column: 'Total_Cost'}, inplace=True)
    
    # Merge to get percentages
    merged_data = group_env_data.merge(group_totals, on=grouping_col)
    merged_data['Percentage'] = merged_data[cost_column] / merged_data['Total_Cost'] * 100
    
    # Identify Production vs Non-Production
    merged_data['Env_Type'] = 'Other'
    merged_data.loc[merged_data[env_column] == 'Prod', 'Env_Type'] = 'Production'
    merged_data.loc[merged_data[env_column].isin(['Dev', 'Stage', 'Test', 'QA']), 'Env_Type'] = 'Non-Production'
    
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


def analyze_hierarchical_env(df, hierarchy_columns, top_n_values=None, nonprod_threshold=20):
    """
    Analyze environment distribution (Prod vs. Non-Prod) through a hierarchical structure.
    
    Args:
        df: DataFrame containing the data
        hierarchy_columns: List of columns representing the organizational hierarchy (e.g., ['cto', 'tr_product_pillar_team'])
        top_n_values: Dictionary of level-specific top_n values (e.g., {'cto': 15, 'tr_product': 10})
                     or a single integer to use the same value for all levels
        nonprod_threshold: Threshold percentage for highlighting high non-production costs
        
    Returns:
        Dictionary with analysis results for each level of the hierarchy
    """
    # Handle top_n_values parameter
    if top_n_values is None:
        # Default to 10 for all levels
        top_n_values = {col: 10 for col in hierarchy_columns}
    elif isinstance(top_n_values, int):
        # Use the same value for all levels
        top_n_values = {col: top_n_values for col in hierarchy_columns}
    # If it's already a dictionary, we'll use it as is
    if df.empty:
        return {'hierarchy_levels': {}, 'nonprod_threshold': nonprod_threshold}
    
    # Dictionary to store results for each hierarchy level
    hierarchy_results = {}
    
    # Analyze each level of the hierarchy
    for column in hierarchy_columns:
        # Skip if column doesn't exist
        if column not in df.columns:
            continue
            
        # Get top_n value for this level
        level_top_n = top_n_values.get(column, 10)
            
        # Perform environment analysis for this level
        level_analysis = analyze_env_by_grouping(df, column, level_top_n, nonprod_threshold)
        
        # Store in results
        hierarchy_results[column] = level_analysis
        
        # Get the top groups at this level (including both high nonprod and top by cost)
        top_groups = set()
        
        # Add high non-prod groups
        if not level_analysis['high_nonprod_groups'].empty:
            top_groups.update(level_analysis['high_nonprod_groups'][column].unique())
        
        # Add top groups by cost
        if not level_analysis['group_env_data'].empty:
            top_cost_groups = level_analysis['group_env_data'].sort_values(
                by='Total_Cost', ascending=False
            ).head(level_top_n)[column].unique()
            top_groups.update(top_cost_groups)
        
        # Don't generate drill-down details - we're removing this feature to simplify
        # Just store the high-level analysis for each hierarchy level
    
    return {
        'hierarchy_levels': hierarchy_results,
        'nonprod_threshold': nonprod_threshold
    }