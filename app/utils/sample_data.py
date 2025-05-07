"""
Sample data generator for when BigQuery is not available.
This provides placeholder data for the dashboard.
"""
import datetime
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
        'day4_cost': [10200.0, 3800.0],
        'day5_cost': [10000.0, 3700.0],
        'percent_change': [2.0, 2.7]
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
    """Create sample daily trend data."""
    # Generate 90 days of data
    end_date = datetime.datetime.now().date() - datetime.timedelta(days=3)
    start_date = end_date - datetime.timedelta(days=90)
    
    dates = [start_date + datetime.timedelta(days=i) for i in range(91)]
    
    # Create data arrays
    daily_data = []
    
    # Base values
    prod_daily_base = 10000
    nonprod_daily_base = 3500
    
    # FY25 averages
    prod_fy25_avg = 9500
    nonprod_fy25_avg = 3000
    
    # FY26 YTD averages
    prod_fy26_ytd_avg = 10200
    nonprod_fy26_ytd_avg = 3600
    
    # FY26 forecasted averages
    prod_fy26_forecast_avg = 11000
    nonprod_fy26_forecast_avg = 3800
    
    # Generate data with some randomness
    for date in dates:
        # Add some seasonality (weekly pattern)
        day_factor = 1.0 + 0.1 * ((date.weekday() % 7) / 10)
        
        # Add some random variation
        random_factor_prod = np.random.normal(1.0, 0.05)
        random_factor_nonprod = np.random.normal(1.0, 0.08)  # More variability in non-prod
        
        # Production data
        daily_data.append({
            'date': date,
            'environment_type': 'PROD',
            'daily_cost': round(prod_daily_base * day_factor * random_factor_prod, 2),
            'fy25_avg_daily_spend': prod_fy25_avg,
            'fy26_ytd_avg_daily_spend': prod_fy26_ytd_avg,
            'fy26_forecasted_avg_daily_spend': prod_fy26_forecast_avg
        })
        
        # Non-production data
        daily_data.append({
            'date': date,
            'environment_type': 'NON-PROD',
            'daily_cost': round(nonprod_daily_base * day_factor * random_factor_nonprod, 2),
            'fy25_avg_daily_spend': nonprod_fy25_avg,
            'fy26_ytd_avg_daily_spend': nonprod_fy26_ytd_avg,
            'fy26_forecasted_avg_daily_spend': nonprod_fy26_forecast_avg
        })
    
    return pd.DataFrame(daily_data)