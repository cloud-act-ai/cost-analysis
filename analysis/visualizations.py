"""
Visualization functions for FinOps reports.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from typing import Dict, List, Tuple, Optional, Any
import base64
from io import BytesIO

def encode_figure_to_base64(fig: Figure) -> str:
    """
    Encode a matplotlib figure to base64 for HTML embedding.
    
    Args:
        fig: Matplotlib figure
        
    Returns:
        Base64 encoded string
    """
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def create_trend_chart(
    trend_data: Dict[str, Any],
    title: str = "Cost Trend",
    y_label: str = "Cost ($)",
    figsize: Tuple[int, int] = (10, 6)
) -> str:
    """
    Create a line chart for cost trends.
    
    Args:
        trend_data: Dictionary containing trend data
        title: Chart title
        y_label: Y-axis label
        figsize: Figure size (width, height) in inches
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Handle different data formats
    if 'trends' in trend_data:
        # Multiple trends (grouped data)
        for trend in trend_data['trends']:
            df = pd.DataFrame(trend['data'])
            ax.plot(df['date'], df['total_cost'], label=trend['name'], marker='o')
    else:
        # Single trend
        df = pd.DataFrame(trend_data['trend'])
        ax.plot(df['date'], df['total_cost'], label='Total Cost', marker='o')
    
    # Identify forecast data if present
    if trend_data.get('has_forecast', False):
        if 'trends' in trend_data:
            for trend in trend_data['trends']:
                df = pd.DataFrame(trend['data'])
                # Assume forecast data comes after actual data
                actual_dates = df['date'][~df['is_forecast']]
                forecast_dates = df['date'][df['is_forecast']]
                forecast_costs = df['total_cost'][df['is_forecast']]
                
                if not forecast_dates.empty:
                    last_actual_date = actual_dates.iloc[-1]
                    # Plot forecast with dotted line
                    ax.plot([last_actual_date] + forecast_dates.tolist(), 
                           [df[df['date'] == last_actual_date]['total_cost'].values[0]] + forecast_costs.tolist(),
                           linestyle='--', marker='o', alpha=0.7, label=f"{trend['name']} (Forecast)")
        else:
            df = pd.DataFrame(trend_data['trend'])
            # Assume forecast data comes after actual data
            actual_dates = df['date'][~df['is_forecast']]
            forecast_dates = df['date'][df['is_forecast']]
            forecast_costs = df['total_cost'][df['is_forecast']]
            
            if not forecast_dates.empty:
                last_actual_date = actual_dates.iloc[-1]
                # Plot forecast with dotted line
                ax.plot([last_actual_date] + forecast_dates.tolist(), 
                       [df[df['date'] == last_actual_date]['total_cost'].values[0]] + forecast_costs.tolist(),
                       linestyle='--', marker='o', alpha=0.7, label='Forecast')
    
    # Format the chart
    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.3)
    
    # Format x-axis to show dates nicely
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=45)
    
    # Add legend if there are multiple lines
    if ('trends' in trend_data and len(trend_data['trends']) > 1) or trend_data.get('has_forecast', False):
        ax.legend()
    
    plt.tight_layout()
    
    # Convert figure to base64 string
    return encode_figure_to_base64(fig)

def create_comparison_chart(
    comparison_data: Dict[str, Any],
    title: str = "Cost Comparison",
    figsize: Tuple[int, int] = (8, 6)
) -> str:
    """
    Create a bar chart for comparing costs between two periods.
    
    Args:
        comparison_data: Dictionary containing comparison data
        title: Chart title
        figsize: Figure size (width, height) in inches
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Extract period names
    period1 = comparison_data.get('period1', 'Period 1')
    period2 = comparison_data.get('period2', 'Period 2')
    
    # Set up bar positions
    bar_width = 0.35
    x = np.arange(len(comparison_data.get('categories', ['Total'])))
    
    # Plot bars for each period
    period1_costs = comparison_data.get('period1_costs', [comparison_data.get('total1', 0)])
    period2_costs = comparison_data.get('period2_costs', [comparison_data.get('total2', 0)])
    
    ax.bar(x - bar_width/2, period1_costs, bar_width, label=period1)
    ax.bar(x + bar_width/2, period2_costs, bar_width, label=period2)
    
    # Add labels, title and legend
    ax.set_xlabel('Category')
    ax.set_ylabel('Cost ($)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(comparison_data.get('categories', ['Total']))
    ax.legend()
    
    # Add value labels on top of each bar
    for i, v in enumerate(period1_costs):
        ax.text(i - bar_width/2, v + 0.1, f'${v:,.2f}', ha='center', va='bottom', fontsize=8)
    
    for i, v in enumerate(period2_costs):
        ax.text(i + bar_width/2, v + 0.1, f'${v:,.2f}', ha='center', va='bottom', fontsize=8)
    
    # Calculate percent change and display it between bars
    for i in range(len(period1_costs)):
        if period1_costs[i] > 0:
            percent_change = ((period2_costs[i] - period1_costs[i]) / period1_costs[i]) * 100
            color = 'red' if percent_change > 0 else 'green'
            ax.text(i, max(period1_costs[i], period2_costs[i]) + 0.5, 
                   f"{percent_change:+.1f}%", ha='center', va='bottom', 
                   color=color, fontweight='bold')
    
    plt.tight_layout()
    
    # Convert figure to base64 string
    return encode_figure_to_base64(fig)

def create_team_comparison_chart(
    team_data: Dict[str, Any],
    title: str = "Product Pillar Team Costs",
    figsize: Tuple[int, int] = (10, 8)
) -> str:
    """
    Create a horizontal bar chart comparing costs across product pillar teams.
    
    Args:
        team_data: Dictionary containing team cost data
        title: Chart title
        figsize: Figure size (width, height) in inches
        
    Returns:
        Base64 encoded image string
    """
    # Extract team names and costs
    teams = [team['name'] for team in team_data.get('teams', [])]
    costs = [team['total_cost'] for team in team_data.get('teams', [])]
    
    # Sort by cost (descending)
    teams_sorted = [x for _, x in sorted(zip(costs, teams), reverse=True)]
    costs_sorted = sorted(costs, reverse=True)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create horizontal bars
    y_pos = np.arange(len(teams_sorted))
    ax.barh(y_pos, costs_sorted)
    
    # Add labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(teams_sorted)
    ax.set_xlabel('Cost ($)')
    ax.set_title(title)
    
    # Add value labels
    for i, v in enumerate(costs_sorted):
        ax.text(v + 0.1, i, f'${v:,.2f}', va='center')
    
    plt.tight_layout()
    
    # Convert figure to base64 string
    return encode_figure_to_base64(fig)

def create_forecast_chart(
    forecast_data: Dict[str, Any],
    title: str = "Cost Forecast",
    figsize: Tuple[int, int] = (10, 6)
) -> str:
    """
    Create a line chart with cost forecast.
    
    Args:
        forecast_data: Dictionary containing actual and forecast data
        title: Chart title
        figsize: Figure size (width, height) in inches
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Extract actual and forecast data
    df = pd.DataFrame(forecast_data.get('data', []))
    
    # Plot actual data
    actual_mask = ~df['is_forecast']
    ax.plot(df['date'][actual_mask], df['total_cost'][actual_mask], 
           label='Actual', marker='o', color='blue')
    
    # Plot forecast data
    forecast_mask = df['is_forecast']
    if any(forecast_mask):
        # Get the last actual data point for smooth transition
        last_actual_idx = actual_mask.sum() - 1
        if last_actual_idx >= 0:
            last_actual_date = df['date'].iloc[last_actual_idx]
            last_actual_cost = df['total_cost'].iloc[last_actual_idx]
            
            # Plot forecast with first point connecting to actual data
            forecast_dates = [last_actual_date] + df['date'][forecast_mask].tolist()
            forecast_costs = [last_actual_cost] + df['total_cost'][forecast_mask].tolist()
            
            ax.plot(forecast_dates, forecast_costs, 
                   label='Forecast', marker='o', linestyle='--', color='orange')
        else:
            # Just plot forecast data if there's no actual data
            ax.plot(df['date'][forecast_mask], df['total_cost'][forecast_mask], 
                   label='Forecast', marker='o', linestyle='--', color='orange')
    
    # Add confidence interval if available
    if 'lower_bound' in df.columns and 'upper_bound' in df.columns:
        forecast_idx = df.index[forecast_mask]
        if len(forecast_idx) > 0:
            ax.fill_between(df['date'][forecast_mask],
                           df['lower_bound'][forecast_mask],
                           df['upper_bound'][forecast_mask],
                           color='orange', alpha=0.2, label='95% Confidence')
    
    # Format the chart
    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel('Cost ($)')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis to show dates nicely
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=45)
    
    # Add legend
    ax.legend()
    
    plt.tight_layout()
    
    # Convert figure to base64 string
    return encode_figure_to_base64(fig)