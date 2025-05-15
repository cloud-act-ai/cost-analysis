"""
Chart configuration for FinOps360 cost analysis dashboard.
"""
from typing import Dict, Any, List, Optional, Union
from app.utils.config_loader import load_config

# Load chart settings from config.yaml
try:
    config = load_config("config.yaml")
    # Get chart enabled setting from config
    CHARTS_ENABLED = config.get('charts', {}).get('enabled', True)
except Exception:
    # Default if config can't be loaded
    CHARTS_ENABLED = True

# Chart dimensions
CHART_HEIGHT = 500
CHART_WIDTH = "100%"

# Colors for chart elements
CHART_COLORS = {
    "PROD": "#3498db",  # Blue
    "NON-PROD": "#2ecc71",  # Green
    "FORECAST": "#f39c12",  # Orange
    "BASELINE": "#95a5a6",  # Gray
    "FY25": "#e74c3c",  # Red
    "FY24": "#9b59b6",  # Purple
    "THRESHOLD_LINE": "#e74c3c",  # Red for threshold lines
}

# Dashboard layout options
CHART_OPTIONS = {
    # Daily trend time series chart
    "daily_trend": {
        "enabled": True,
        "type": "time_series",
        "title": "Daily Cost Analysis for PROD and NON-PROD Environments",
        "x_axis": {
            "title": "Date",
            "range": ["2025-02-01", "2026-01-31"],  # Feb 2025 to Jan 2026
            "forecast_date": "current_date",  # Mark forecast line at current date
        },
        "y_axis": {
            "title": "Daily Cost ($)",
            "start_at_zero": True,
            "format": "currency",  # Format as currency
        },
        "series": [
            {
                "name": "PROD Daily Cost (FY26)",
                "column": "daily_cost",
                "filter": {"environment_type": "PROD"},
                "color": CHART_COLORS["PROD"],
                "type": "line",
            },
            {
                "name": "NON-PROD Daily Cost (FY26)",
                "column": "daily_cost",
                "filter": {"environment_type": "NON-PROD"},
                "color": CHART_COLORS["NON-PROD"],
                "type": "line",
            },
            {
                "name": "FY26 Avg Daily Spend",
                "column": "fy26_avg_daily_spend",
                "filter": {"environment_type": "PROD"},
                "color": CHART_COLORS["BASELINE"],
                "type": "line",
                "dash": "dash",
            },
            {
                "name": "FY25 Avg Daily Spend",
                "column": "fy25_avg_daily_spend",
                "filter": {"environment_type": "PROD"},
                "color": CHART_COLORS["FY25"],
                "type": "line",
                "dash": "dash",
            },
        ],
        "annotations": [
            {
                "type": "vline",
                "x": "current_date",
                "line": {"color": CHART_COLORS["THRESHOLD_LINE"], "dash": "dash"},
                "annotation_text": "Current Date",
            }
        ],
    },
    
    # CTO costs horizontal stacked bar chart
    "cto_costs": {
        "enabled": True,
        "type": "horizontal_stacked_bar",
        "title": "CTO Organization Costs",
        "y_axis": {
            "title": "CTO Organization",
            "column": "cto_org",
        },
        "x_axis": {
            "title": "Cost ($)",
            "start_at_zero": True,
            "format": "currency",
        },
        "series": [
            {
                "name": "PROD Costs",
                "column": "prod_ytd_cost",
                "color": CHART_COLORS["PROD"],
                "show_percentage": True,
            },
            {
                "name": "NON-PROD Costs",
                "column": "nonprod_ytd_cost",
                "color": CHART_COLORS["NON-PROD"],
                "show_percentage": True,
            },
        ],
        "sort_by": {"column": "total_ytd_cost", "direction": "descending"},
    },
    
    # Pillar costs horizontal stacked bar chart
    "pillar_costs": {
        "enabled": True,
        "type": "horizontal_stacked_bar",
        "title": "Product Pillar Team Costs",
        "y_axis": {
            "title": "Pillar Team",
            "column": "pillar_name",
        },
        "x_axis": {
            "title": "Cost ($)",
            "start_at_zero": True,
            "format": "currency",
        },
        "series": [
            {
                "name": "PROD Costs",
                "column": "prod_ytd_cost",
                "color": CHART_COLORS["PROD"],
                "show_percentage": True,
            },
            {
                "name": "NON-PROD Costs",
                "column": "nonprod_ytd_cost",
                "color": CHART_COLORS["NON-PROD"],
                "show_percentage": True,
            },
        ],
        "sort_by": {"column": "total_ytd_cost", "direction": "descending"},
    },
    
    # Product costs horizontal stacked bar chart (top N products)
    "product_costs": {
        "enabled": True,
        "type": "horizontal_stacked_bar",
        "title": "Top Product Costs",
        "y_axis": {
            "title": "Product ID",
            "column": "product_id",
        },
        "x_axis": {
            "title": "Cost ($)",
            "start_at_zero": True,
            "format": "currency",
        },
        "series": [
            {
                "name": "PROD Costs",
                "column": "prod_ytd_cost",
                "color": CHART_COLORS["PROD"],
                "show_percentage": True,
            },
            {
                "name": "NON-PROD Costs",
                "column": "nonprod_ytd_cost",
                "color": CHART_COLORS["NON-PROD"],
                "show_percentage": True,
            },
        ],
        "sort_by": {"column": "total_ytd_cost", "direction": "descending"},
        "limit": 10,  # Show only top 10 products
    },
}

# Helper functions to access chart configuration
def get_chart_config(chart_key: str) -> Dict[str, Any]:
    """Get configuration for a specific chart."""
    return CHART_OPTIONS.get(chart_key, {})

def is_chart_enabled(chart_key: str) -> bool:
    """Check if a specific chart is enabled."""
    if not CHARTS_ENABLED:
        return False
    chart_config = get_chart_config(chart_key)
    return chart_config.get("enabled", False)

def are_charts_enabled() -> bool:
    """Check if charts are globally enabled."""
    return CHARTS_ENABLED

def get_chart_dimensions() -> Dict[str, Union[int, str]]:
    """Get standard chart dimensions."""
    return {
        "height": CHART_HEIGHT,
        "width": CHART_WIDTH,
    }

def get_chart_colors() -> Dict[str, str]:
    """Get chart color palette."""
    return CHART_COLORS