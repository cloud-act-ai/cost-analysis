"""
Default configuration values for the FinOps360 dashboard.
"""

# Default application title
DEFAULT_TITLE = "FinOps360 Cost Analysis Tool"

# Default display settings
DEFAULT_DISPLAY_SETTINGS = {
    "display_millions": True,
    "nonprod_percentage_threshold": 30,
    "top_products_count": 10
}

# Default color scheme
DEFAULT_COLORS = {
    "primary": "#3498db",  # Primary blue
    "secondary": "#2ecc71",  # Green
    "accent": "#f39c12",  # Orange
    "danger": "#e74c3c",  # Red
    "neutral": "#95a5a6",  # Gray
    "dark": "#2c3e50",  # Dark blue
    "light": "#f5f7f9"   # Light gray background
}

# Default date ranges for comparisons
DEFAULT_DATE_RANGES = {
    "day_current_date": "2025-05-03",
    "day_previous_date": "2025-05-02",
    "week_current_start": "2025-04-27",
    "week_current_end": "2025-05-03",
    "week_previous_start": "2025-04-20",
    "week_previous_end": "2025-04-26",
    "month_current": "2025-04",
    "month_previous": "2025-03"
}

# Default fiscal year settings
DEFAULT_FISCAL_YEAR = {
    "fy_start_date": "2025-02-01",
    "fy_end_date": "2026-01-31"
}

def get_default_config():
    """
    Get the default configuration as a dictionary.
    
    Returns:
        Dictionary with default configuration values
    """
    return {
        "dashboard": {
            "title": DEFAULT_TITLE,
            "subtitle": "Comprehensive Cloud Cost Analysis",
            "logo_path": None,
            "theme": "light"
        },
        "display": DEFAULT_DISPLAY_SETTINGS,
        "colors": DEFAULT_COLORS,
        "dates": DEFAULT_DATE_RANGES,
        "fiscal_year": DEFAULT_FISCAL_YEAR
    }