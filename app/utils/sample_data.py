"""
Sample data generator for when BigQuery is not available.
This provides placeholder data for the dashboard.
"""
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple


def create_sample_ytd_costs() -> pd.DataFrame:
    """Create sample year-to-date costs DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'ytd_cost': [207944.33, 85000.0],
        'days': [120, 120]
    }
    return pd.DataFrame(data)


def create_sample_fy26_ytd_costs() -> pd.DataFrame:
    """Create sample FY26 year-to-date costs DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'ytd_cost': [1250000.0, 450000.0],
        'days': [90, 90]  # Assuming 90 days since start of FY26
    }
    return pd.DataFrame(data)


def create_sample_fy26_costs() -> pd.DataFrame:
    """Create sample FY26 costs DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'total_cost': [3800000.0, 1200000.0],
        'days': [365, 365]
    }
    return pd.DataFrame(data)


def create_sample_fy25_costs() -> pd.DataFrame:
    """Create sample FY25 costs DataFrame with ytd_cost values."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'total_cost': [3500000.0, 1050000.0],
        'ytd_cost': [750356.72, 290000.0],  # YTD costs for same period in FY25
        'days': [365, 365]
    }
    return pd.DataFrame(data)


def create_sample_day_comparison() -> pd.DataFrame:
    """Create sample day-to-day comparison DataFrame with specific dates."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'day_current_cost': [10200.0, 3800.0],
        'day_previous_cost': [10000.0, 3700.0],
        'percent_change': [2.0, 2.7]
    }
    return pd.DataFrame(data)


def create_sample_week_comparison() -> pd.DataFrame:
    """Create sample week-to-week comparison DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'this_week_cost': [72000.0, 26000.0],
        'prev_week_cost': [70000.0, 24000.0],
        'percent_change': [2.9, 8.3],
        'this_week_start': ['2025-04-27', '2025-04-27'],
        'this_week_end': ['2025-05-03', '2025-05-03'],
        'prev_week_start': ['2025-04-20', '2025-04-20'],
        'prev_week_end': ['2025-04-26', '2025-04-26']
    }
    return pd.DataFrame(data)


def create_sample_month_comparison() -> pd.DataFrame:
    """Create sample month-to-month comparison DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'this_month_cost': [310000.0, 110000.0],
        'prev_month_cost': [300000.0, 100000.0],
        'percent_change': [3.3, 10.0],
        'this_month': ['Apr 2025', 'Apr 2025'],
        'prev_month': ['Mar 2025', 'Mar 2025']
    }
    return pd.DataFrame(data)


def create_sample_date_info() -> Dict[str, str]:
    """Create sample date information for the template using dynamic dates."""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Calculate week dates
    current_week_end = today - timedelta(days=today.weekday() + 1)  # Last Saturday
    current_week_start = current_week_end - timedelta(days=6)  # Previous Sunday
    previous_week_end = current_week_start - timedelta(days=1)  # Saturday before current_week_start
    previous_week_start = previous_week_end - timedelta(days=6)  # Sunday before previous_week_end

    # Calculate month dates
    current_month = today.replace(day=1)
    previous_month = (current_month - timedelta(days=1)).replace(day=1)

    return {
        'day_current_date': today.strftime('%Y-%m-%d'),
        'day_previous_date': yesterday.strftime('%Y-%m-%d'),
        'week_current_date_range': f"{current_week_start.strftime('%b %d')} - {current_week_end.strftime('%b %d, %Y')}",
        'week_previous_date_range': f"{previous_week_start.strftime('%b %d')} - {previous_week_end.strftime('%b %d, %Y')}",
        'month_current_date_range': current_month.strftime('%b %Y'),
        'month_previous_date_range': previous_month.strftime('%b %Y')
    }


def create_sample_product_costs() -> pd.DataFrame:
    """Create sample product costs DataFrame."""
    # Create sample data for 10 products
    products = [f"PROD-{i+1000}" for i in range(10)]
    names = [f"Product {i+1}" for i in range(10)]
    teams = ["Platform", "Customer", "Infrastructure", "Data", "Security"] * 2
    
    # Calculate costs - higher for first products
    prod_costs = [100000 - i*8000 for i in range(10)]
    nonprod_costs = [40000 - i*3000 for i in range(10)]
    total_costs = [p + n for p, n in zip(prod_costs, nonprod_costs)]
    percentages = [(n / t) * 100 for n, t in zip(nonprod_costs, total_costs)]
    
    # Create display_id field by combining pillar team and product ID
    display_ids = [f"{team} - {product}" for team, product in zip(teams, products)]
    
    data = {
        'product_id': products,
        'product_name': names,
        'pillar_team': teams,
        'display_id': display_ids,
        'prod_ytd_cost': prod_costs,
        'nonprod_ytd_cost': nonprod_costs,
        'total_ytd_cost': total_costs,
        'nonprod_percentage': percentages
    }
    
    return pd.DataFrame(data)


def create_sample_cto_costs() -> pd.DataFrame:
    """Create sample CTO costs DataFrame."""
    # Create sample data for 5 CTO organizations
    cto_orgs = ["Core Tech", "Digital", "Enterprise", "Platform", "Infrastructure"]
    
    # Calculate costs - higher for first CTOs
    prod_costs = [320000, 280000, 240000, 200000, 180000]
    nonprod_costs = [130000, 110000, 90000, 70000, 60000]
    total_costs = [p + n for p, n in zip(prod_costs, nonprod_costs)]
    percentages = [(n / t) * 100 for n, t in zip(nonprod_costs, total_costs)]
    
    data = {
        'cto_org': cto_orgs,
        'prod_ytd_cost': prod_costs,
        'nonprod_ytd_cost': nonprod_costs,
        'total_ytd_cost': total_costs,
        'nonprod_percentage': percentages
    }
    
    return pd.DataFrame(data)


def create_sample_pillar_costs() -> pd.DataFrame:
    """Create sample pillar costs DataFrame."""
    # Create sample data for 5 pillar teams
    pillar_names = ["Platform", "Customer", "Infrastructure", "Data", "Security"]
    product_counts = [8, 12, 7, 10, 5]
    
    # Calculate costs - higher for first pillars
    prod_costs = [280000, 230000, 190000, 160000, 120000]
    nonprod_costs = [110000, 95000, 80000, 65000, 50000]
    total_costs = [p + n for p, n in zip(prod_costs, nonprod_costs)]
    
    data = {
        'pillar_name': pillar_names,
        'product_count': product_counts,
        'prod_ytd_cost': prod_costs,
        'nonprod_ytd_cost': nonprod_costs,
        'total_ytd_cost': total_costs
    }
    
    return pd.DataFrame(data)


def create_sample_daily_trend_data() -> pd.DataFrame:
    """Create sample daily trend data that matches the enhanced chart structure."""
    # Use current year for more dynamic data
    current_year = datetime.now().year
    # Generate a full year of data
    start_date = datetime(current_year-1, 2, 1).date()  # Start of previous FY
    end_date = datetime(current_year, 1, 31).date()  # End of previous FY
    
    days_total = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(days_total)]
    
    # Create data arrays
    daily_data = []
    
    # Base values (designed to match sample data)
    prod_daily_base = 250000
    nonprod_daily_base = 50000
    
    # FY25 averages (historical)
    prod_fy25_avg = 200000
    nonprod_fy25_avg = 45000
    
    # FY24 averages (historical)
    prod_fy24_avg = 150000
    nonprod_fy24_avg = 40000
    
    # Current date for forecast cutoff
    current_date = datetime.now().date()
    if current_date < start_date:
        current_date = start_date + timedelta(days=90)  # Use a fixed date if we're before FY26
    
    # Generate data with characteristic spikes and patterns
    for i, date in enumerate(dates):
        # Add some seasonality 
        month_factor = 1.0 + 0.05 * np.sin(i / 30 * np.pi)  # Monthly cycle
        
        # Add spikes in the first few months
        spike_factor = 1.0
        if i < 90:
            # Random spikes in the first 3 months
            if i % 14 == 0 or i % 23 == 0:
                spike_factor = np.random.choice([1.2, 1.3, 1.4, 1.5])
            
            # Add a few major spikes
            if i in [15, 35, 50, 65]:
                spike_factor = np.random.uniform(1.3, 1.6)
        
        # Add some random variation (higher variance in early months)
        random_var = 0.02 if i > 90 else 0.05
        random_factor_prod = np.random.normal(1.0, random_var)
        random_factor_nonprod = np.random.normal(1.0, random_var)
        
        # Gradually normalize the pattern after first three months
        if i >= 90:
            # More stable pattern in later months
            day_factor = 1.0 + 0.03 * np.sin(i / 7 * np.pi)  # Weekly pattern
            spike_factor = 1.0 + 0.02 * np.sin(i / 15 * np.pi)  # Bi-weekly pattern
        else:
            day_factor = 1.0 + 0.08 * ((date.weekday() % 7) / 10)
        
        # Compute final cost with all factors
        prod_cost = prod_daily_base * day_factor * month_factor * spike_factor * random_factor_prod
        nonprod_cost = nonprod_daily_base * day_factor * month_factor * spike_factor * random_factor_nonprod
        
        # Make sure May 2nd and May 3rd 2025 have specific values for comparisons
        if date == date(2025, 5, 3):
            prod_cost = 12000.0
            nonprod_cost = 3800.0
        elif date == date(2025, 5, 2):
            prod_cost = 11500.0
            nonprod_cost = 3700.0
        
        # Generate FY25 baseline costs with a similar pattern but lower values
        fy25_month_factor = 1.0 + 0.04 * np.sin(i / 28 * np.pi)  # Slightly different cycle
        fy25_spike_factor = 1.0
        if i % 17 == 0 or i % 29 == 0:
            fy25_spike_factor = np.random.choice([1.15, 1.25, 1.35])
        
        fy25_prod_cost = prod_fy25_avg * fy25_month_factor * fy25_spike_factor
        fy25_nonprod_cost = nonprod_fy25_avg * fy25_month_factor * fy25_spike_factor
        
        # Generate FY24 baseline costs
        fy24_month_factor = 1.0 + 0.03 * np.sin(i / 26 * np.pi)  # Different cycle again
        fy24_prod_cost = prod_fy24_avg * fy24_month_factor
        fy24_nonprod_cost = nonprod_fy24_avg * fy24_month_factor
        
        # No forecast generation needed
        
        # Production data
        daily_data.append({
            'date': date,
            'environment_type': 'PROD',
            'daily_cost': round(prod_cost, 2),
            'fy26_avg_daily_spend': round(prod_daily_base, 2),  # Constant average line
            'fy25_avg_daily_spend': round(prod_fy25_avg, 2),  # Constant baseline
            'fy24_avg_daily_spend': round(prod_fy24_avg, 2),  # Constant baseline
            'fy26_ytd_avg_daily_spend': round(prod_cost, 2) if date <= current_date else 0.0
        })

        # Non-production data
        daily_data.append({
            'date': date,
            'environment_type': 'NON-PROD',
            'daily_cost': round(nonprod_cost, 2),
            'fy26_avg_daily_spend': round(nonprod_daily_base, 2),  # Constant average line
            'fy25_avg_daily_spend': round(fy25_nonprod_cost, 2),
            'fy24_avg_daily_spend': round(fy24_nonprod_cost, 2),
            'fy26_ytd_avg_daily_spend': round(nonprod_cost, 2) if date <= current_date else 0.0
        })
    
    return pd.DataFrame(daily_data)