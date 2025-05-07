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
        'ytd_cost': [1250000.0, 450000.0],
        'days': [120, 120]
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
    """Create sample FY25 costs DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'total_cost': [3500000.0, 1050000.0],
        'days': [365, 365]
    }
    return pd.DataFrame(data)


def create_sample_day_comparison() -> pd.DataFrame:
    """Create sample day-to-day comparison DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'day_current_cost': [10200.0, 3800.0],
        'day_previous_cost': [10000.0, 3700.0],
        'percent_change': [2.0, 2.7],
        'compare_date': [date.today() - timedelta(days=4), date.today() - timedelta(days=4)]
    }
    return pd.DataFrame(data)


def create_sample_week_comparison() -> pd.DataFrame:
    """Create sample week-to-week comparison DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'this_week_cost': [72000.0, 26000.0],
        'prev_week_cost': [70000.0, 24000.0],
        'percent_change': [2.9, 8.3]
    }
    return pd.DataFrame(data)


def create_sample_month_comparison() -> pd.DataFrame:
    """Create sample month-to-month comparison DataFrame."""
    data = {
        'environment_type': ['PROD', 'NON-PROD'],
        'this_month_cost': [310000.0, 110000.0],
        'prev_month_cost': [300000.0, 100000.0],
        'percent_change': [3.3, 10.0]
    }
    return pd.DataFrame(data)


def create_sample_date_info() -> Dict[str, str]:
    """Create sample date information for the template."""
    today = date.today()
    
    # Calculate sample dates based on typical offsets
    day_current = today - timedelta(days=4)
    day_previous = today - timedelta(days=5)
    
    this_week_start = today - timedelta(days=today.weekday() + 7)
    this_week_end = this_week_start + timedelta(days=6)
    prev_week_start = this_week_start - timedelta(days=7)
    prev_week_end = prev_week_start + timedelta(days=6)
    
    # Get current month and previous month
    if today.month == 1:
        this_month = date(today.year - 1, 12, 1)
    else:
        this_month = date(today.year, today.month - 1, 1)
        
    if this_month.month == 1:
        prev_month = date(this_month.year - 1, 12, 1)
    else:
        prev_month = date(this_month.year, this_month.month - 1, 1)
    
    return {
        'day_current_date': day_current.strftime('%Y-%m-%d'),
        'day_previous_date': day_previous.strftime('%Y-%m-%d'),
        'week_current_date_range': f"{this_week_start.strftime('%b %d')} - {this_week_end.strftime('%b %d, %Y')}",
        'week_previous_date_range': f"{prev_week_start.strftime('%b %d')} - {prev_week_end.strftime('%b %d, %Y')}",
        'month_current_date_range': f"{this_month.strftime('%b %Y')}",
        'month_previous_date_range': f"{prev_month.strftime('%b %Y')}"
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
    
    data = {
        'product_id': products,
        'product_name': names,
        'pillar_team': teams,
        'prod_ytd_cost': prod_costs,
        'nonprod_ytd_cost': nonprod_costs,
        'total_ytd_cost': total_costs,
        'nonprod_percentage': percentages
    }
    
    return pd.DataFrame(data)


def create_sample_daily_trend_data() -> pd.DataFrame:
    """Create sample daily trend data that resembles the image pattern."""
    # Generate a full year of data (FY26)
    start_date = datetime.datetime(2025, 2, 1).date()  # Start of FY26
    end_date = datetime.datetime(2026, 1, 31).date()  # End of FY26
    
    days_total = (end_date - start_date).days + 1
    dates = [start_date + datetime.timedelta(days=i) for i in range(days_total)]
    
    # Create data arrays
    daily_data = []
    
    # Base values (designed to match the image)
    prod_daily_base = 250000
    nonprod_daily_base = 50000
    
    # FY25 averages (historical)
    prod_fy25_avg = 200000
    nonprod_fy25_avg = 45000
    
    # FY26 YTD averages
    prod_fy26_ytd_avg = 240000
    nonprod_fy26_ytd_avg = 48000
    
    # FY26 forecasted averages
    prod_fy26_forecast_avg = 245000
    nonprod_fy26_forecast_avg = 50000
    
    # Generate data with characteristic spikes and patterns
    for i, date in enumerate(dates):
        # Add some seasonality 
        month_factor = 1.0 + 0.05 * np.sin(i / 30 * np.pi)  # Monthly cycle
        
        # Add spikes in the first few months to match the image
        spike_factor = 1.0
        if i < 90:
            # Random spikes in the first 3 months (similar to image)
            if i % 14 == 0 or i % 23 == 0:
                spike_factor = np.random.choice([1.2, 1.3, 1.4, 1.5])
            
            # Add a few major spikes
            if i in [15, 35, 50, 65]:
                spike_factor = np.random.uniform(1.3, 1.6)
        
        # Add some random variation (higher variance in early months)
        random_var = 0.02 if i > 90 else 0.05
        random_factor_prod = np.random.normal(1.0, random_var)
        random_factor_nonprod = np.random.normal(1.0, random_var)
        
        # Gradually normalize the pattern after first three months to match the image
        if i >= 90:
            # More stable pattern in later months, matching the image
            day_factor = 1.0 + 0.03 * np.sin(i / 7 * np.pi)  # Weekly pattern
            spike_factor = 1.0 + 0.02 * np.sin(i / 15 * np.pi)  # Bi-weekly pattern
        else:
            day_factor = 1.0 + 0.08 * ((date.weekday() % 7) / 10)
        
        # Compute final cost with all factors
        prod_cost = prod_daily_base * day_factor * month_factor * spike_factor * random_factor_prod
        nonprod_cost = nonprod_daily_base * day_factor * month_factor * spike_factor * random_factor_nonprod
        
        # Production data
        daily_data.append({
            'date': date,
            'environment_type': 'PROD',
            'daily_cost': round(prod_cost, 2),
            'fy25_avg_daily_spend': prod_fy25_avg,
            'fy26_ytd_avg_daily_spend': prod_fy26_ytd_avg,
            'fy26_forecasted_avg_daily_spend': prod_fy26_forecast_avg
        })
        
        # Non-production data
        daily_data.append({
            'date': date,
            'environment_type': 'NON-PROD',
            'daily_cost': round(nonprod_cost, 2),
            'fy25_avg_daily_spend': nonprod_fy25_avg,
            'fy26_ytd_avg_daily_spend': nonprod_fy26_ytd_avg,
            'fy26_forecasted_avg_daily_spend': nonprod_fy26_forecast_avg
        })
    
    return pd.DataFrame(daily_data)