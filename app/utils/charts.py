"""
Chart generation utilities for FinOps360 cost analysis dashboard.
"""
import logging
import base64
import json
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

logger = logging.getLogger(__name__)

def encode_figure_to_base64(fig: plt.Figure) -> str:
    """
    Encode a matplotlib figure to base64 for embedding in HTML.
    
    Args:
        fig: Matplotlib figure
        
    Returns:
        Base64-encoded string
    """
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def create_daily_trend_chart(df: pd.DataFrame) -> str:
    """
    Create a daily trend chart with both actual and forecasted costs.
    
    Args:
        df: DataFrame with daily cost data
        
    Returns:
        Base64-encoded chart image
    """
    try:
        # Check if dataframe is empty
        if df.empty:
            # Create empty chart with message
            plt.style.use('ggplot')
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, 'No data available for trend chart', 
                   ha='center', va='center', fontsize=14)
            ax.set_title('Daily Cost Analysis for PROD and NON-PROD Environments', fontsize=14)
            plt.tight_layout()
            return encode_figure_to_base64(fig)
            
        # Use a cleaner style for the plot
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Define colors
        prod_color = '#3366cc'  # Blue for PROD
        nonprod_color = '#33aa33'  # Green for NON-PROD
        avg_color = '#666666'  # Gray for averages
        forecast_prod_color = '#9966ff'  # Purple for PROD forecast
        forecast_nonprod_color = '#ff6666'  # Red for NON-PROD forecast
        
        # Set title at the top
        fig.suptitle('FY26 Daily Cost for PROD and NON-PROD (Including Forecast)', fontsize=14, y=0.98)
        
        # Plot each environment type
        legend_handles = []
        legend_labels = []
        
        # Plot each environment type
        for env, group in df.groupby('environment_type'):
            color = prod_color if env == 'PROD' else nonprod_color
            forecast_color = forecast_prod_color if env == 'PROD' else forecast_nonprod_color
            
            # Plot actual daily cost
            line1, = ax.plot(
                group['date'], 
                group['daily_cost'], 
                linewidth=1.5,
                color=color,
                alpha=0.9
            )
            legend_handles.append(line1)
            legend_labels.append(f"{env} Daily Cost (FY26)")
            
            # Add FY25 average (historical baseline)
            line2, = ax.plot(
                group['date'], 
                group['fy25_avg_daily_spend'], 
                linestyle='--',
                linewidth=1,
                color='#999999',
                alpha=0.7
            )
            legend_handles.append(line2)
            legend_labels.append("FY25 Avg Daily Spend")
            
            # Add FY26 YTD average
            line3, = ax.plot(
                group['date'], 
                group['fy26_ytd_avg_daily_spend'], 
                linestyle='-.',
                linewidth=1,
                color=avg_color,
                alpha=0.8
            )
            legend_handles.append(line3)
            legend_labels.append("FY26 Avg Daily Spend")
            
            # Add forecasted line
            line4, = ax.plot(
                group['date'], 
                group['fy26_forecasted_avg_daily_spend'], 
                linestyle=':',
                linewidth=2,
                color=forecast_color,
                alpha=0.9
            )
            legend_handles.append(line4)
            legend_labels.append(f"{env} Forecasted Daily Cost (FY26)")
                
        # Format the plot
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cost ($)', fontsize=12)
        
        # Add gridlines
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Format date labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        fig.autofmt_xdate(rotation=45)
        
        # Add legend in a good position
        ax.legend(handles=legend_handles, labels=legend_labels, loc='upper right', 
                 bbox_to_anchor=(1.01, 1), fontsize=10)
        
        # Show y-axis in dollar format
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
        
        plt.tight_layout()
        return encode_figure_to_base64(fig)
    
    except Exception as e:
        logger.error(f"Error creating daily trend chart: {e}")
        return ""

def create_forecast_chart(df: pd.DataFrame) -> str:
    """
    Create a chart showing actual vs forecasted costs.
    
    Args:
        df: DataFrame with forecasting data
        
    Returns:
        Base64-encoded chart image
    """
    try:
        # Check if dataframe is empty
        if df.empty:
            # Create empty chart with message
            plt.style.use('ggplot')
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No data available for forecast chart', 
                   ha='center', va='center', fontsize=14)
            ax.set_title('Cost Forecast (Next 30 Days)', fontsize=14)
            plt.tight_layout()
            return encode_figure_to_base64(fig)
            
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(10, 6))
        legend_handles = []
        legend_labels = []
        
        # Plot each environment type with actual vs forecasted
        for env, group in df.groupby('environment_type'):
            # Plot actual daily cost
            line1, = ax.plot(
                group['date'],
                group['daily_cost'],
                marker='o',
                markersize=4,
                linewidth=2
            )
            legend_handles.append(line1)
            legend_labels.append(f"{env} Actual")
            
            # Plot forecasted average
            if 'fy26_forecasted_avg_daily_spend' in group.columns:
                # Filter to non-null forecast values
                forecast_data = group[group['fy26_forecasted_avg_daily_spend'].notnull()]
                
                if not forecast_data.empty:
                    line2, = ax.plot(
                        forecast_data['date'],
                        forecast_data['fy26_forecasted_avg_daily_spend'],
                        linestyle='--',
                        linewidth=1.5
                    )
                    legend_handles.append(line2)
                    legend_labels.append(f"{env} Forecast")
                    
                    # Add shaded area for +/- 10% confidence interval
                    ax.fill_between(
                        forecast_data['date'],
                        forecast_data['fy26_forecasted_avg_daily_spend'] * 0.9,
                        forecast_data['fy26_forecasted_avg_daily_spend'] * 1.1,
                        alpha=0.2
                    )
        
        # Format the plot
        ax.set_title('Cost Forecast (Next 30 Days)', fontsize=14)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cost ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format date labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        fig.autofmt_xdate()
        
        # Add legend manually
        if legend_handles:
            ax.legend(legend_handles, legend_labels)
        
        plt.tight_layout()
        return encode_figure_to_base64(fig)
    
    except Exception as e:
        logger.error(f"Error creating forecast chart: {e}")
        return ""

def create_environment_breakdown_chart(prod_df: pd.DataFrame, nonprod_df: pd.DataFrame) -> str:
    """
    Create a chart showing environment cost breakdown.
    
    Args:
        prod_df: DataFrame with production cost data
        nonprod_df: DataFrame with non-production cost data
        
    Returns:
        Base64-encoded chart image
    """
    try:
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Check if we have data
        has_prod_data = not prod_df.empty and 'ytd_cost' in prod_df.columns
        has_nonprod_data = not nonprod_df.empty and 'ytd_cost' in nonprod_df.columns
        
        if not (has_prod_data or has_nonprod_data):
            # No data available, create empty chart with message
            ax.text(0.5, 0.5, 'No environment cost data available', 
                   ha='center', va='center', fontsize=14)
            ax.set_title('Cost Breakdown by Environment', fontsize=14)
            plt.tight_layout()
            return encode_figure_to_base64(fig)
        
        # Prepare data
        environments = ['PROD', 'NON-PROD']
        ytd_costs = [
            prod_df['ytd_cost'].iloc[0] if has_prod_data else 0,
            nonprod_df['ytd_cost'].iloc[0] if has_nonprod_data else 0
        ]
        
        # Create bars for YTD costs
        bars = ax.bar(environments, ytd_costs, label='YTD Actual')
        
        # Add value labels
        for i, cost in enumerate(ytd_costs):
            if cost > 0:
                ax.text(i, cost / 2, f'${cost:,.0f}', ha='center', va='center', 
                       color='white', fontweight='bold')
            
        # Add percentage breakdown
        total = sum(ytd_costs)
        if total > 0:
            percentages = [cost / total * 100 for cost in ytd_costs]
            
            for i, percentage in enumerate(percentages):
                if ytd_costs[i] > 0:
                    ax.text(i, ytd_costs[i] + (max(ytd_costs) * 0.02 if max(ytd_costs) > 0 else 1), 
                           f"{percentage:.1f}%", ha='center', va='bottom')
        
        # Format the plot
        ax.set_title('Cost Breakdown by Environment', fontsize=14)
        ax.set_ylabel('Cost ($)', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add legend if we have data
        if total > 0:
            ax.legend([bars[0]], ['YTD Actual'])
        
        plt.tight_layout()
        return encode_figure_to_base64(fig)
    
    except Exception as e:
        logger.error(f"Error creating environment breakdown chart: {e}")
        return ""

def create_product_breakdown_chart(product_df: pd.DataFrame, top_n: int = 10) -> str:
    """
    Create a chart showing top products by cost.
    
    Args:
        product_df: DataFrame with product cost data
        top_n: Number of top products to display
        
    Returns:
        Base64-encoded chart image
    """
    try:
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Check for empty dataframe or missing columns
        required_columns = ['product_name', 'total_ytd_cost', 'prod_ytd_cost', 'nonprod_ytd_cost']
        has_required_data = (not product_df.empty and 
                            all(col in product_df.columns for col in ['product_name', 'environment']) and
                            ('total_ytd_cost' in product_df.columns or 'prod_ytd_cost' in product_df.columns))
        
        if not has_required_data:
            # Create empty chart with message
            ax.text(0.5, 0.5, 'No product cost data available', 
                   ha='center', va='center', fontsize=14)
            ax.set_title('Top Products by Cost', fontsize=14)
            plt.tight_layout()
            return encode_figure_to_base64(fig)
        
        # Ensure we have the necessary cost columns or create them
        if 'total_ytd_cost' not in product_df.columns and 'prod_ytd_cost' in product_df.columns and 'nonprod_ytd_cost' in product_df.columns:
            product_df['total_ytd_cost'] = product_df['prod_ytd_cost'] + product_df['nonprod_ytd_cost']
        
        if 'prod_ytd_cost' not in product_df.columns:
            product_df['prod_ytd_cost'] = product_df.apply(
                lambda row: row['total_ytd_cost'] if row.get('environment', '') == 'PROD' else 0, 
                axis=1
            )
            
        if 'nonprod_ytd_cost' not in product_df.columns:
            product_df['nonprod_ytd_cost'] = product_df.apply(
                lambda row: row['total_ytd_cost'] if row.get('environment', '') == 'NON-PROD' else 0, 
                axis=1
            )
        
        # Get top N products by total cost
        sort_column = 'total_ytd_cost' if 'total_ytd_cost' in product_df.columns else 'prod_ytd_cost'
        top_products = product_df.sort_values(sort_column, ascending=False).head(top_n)
        
        # If we need to aggregate by product and environment
        if len(top_products) > 0 and 'environment' in top_products.columns:
            # Create a summary dataframe with one row per product
            summary = []
            for product_name in top_products['product_name'].unique():
                product_rows = top_products[top_products['product_name'] == product_name]
                
                prod_cost = product_rows[product_rows['environment'] == 'PROD']['prod_ytd_cost'].sum() if 'prod_ytd_cost' in product_rows.columns else 0
                nonprod_cost = product_rows[product_rows['environment'] == 'NON-PROD']['nonprod_ytd_cost'].sum() if 'nonprod_ytd_cost' in product_rows.columns else 0
                
                if 'total_ytd_cost' in product_rows.columns:
                    total_cost = product_rows['total_ytd_cost'].sum()
                else:
                    total_cost = prod_cost + nonprod_cost
                
                summary.append({
                    'product_name': product_name,
                    'prod_ytd_cost': prod_cost,
                    'nonprod_ytd_cost': nonprod_cost,
                    'total_ytd_cost': total_cost
                })
            
            if summary:
                # Convert to DataFrame and sort
                summary_df = pd.DataFrame(summary)
                top_products = summary_df.sort_values('total_ytd_cost', ascending=True)
        else:
            # Sort in ascending order for horizontal bar chart (bottom to top)
            top_products = top_products.sort_values('total_ytd_cost', ascending=True)
        
        # Check if we have any products
        if top_products.empty:
            ax.text(0.5, 0.5, 'No product cost data available', 
                   ha='center', va='center', fontsize=14)
            ax.set_title('Top Products by Cost', fontsize=14)
            plt.tight_layout()
            return encode_figure_to_base64(fig)
        
        # Get product names and costs
        products = top_products['product_name'].tolist()
        prod_costs = top_products['prod_ytd_cost'].tolist() 
        nonprod_costs = top_products['nonprod_ytd_cost'].tolist()
        
        # Create horizontal stacked bars
        y_pos = np.arange(len(products))
        prod_bars = ax.barh(y_pos, prod_costs, label='PROD')
        nonprod_bars = ax.barh(y_pos, nonprod_costs, left=prod_costs, label='NON-PROD')
        
        # Add labels
        ax.set_yticks(y_pos)
        ax.set_yticklabels(products)
        ax.set_xlabel('Cost ($)', fontsize=12)
        ax.set_title('Top Products by Cost', fontsize=14)
        
        # Add value labels
        for i, (prod, nonprod) in enumerate(zip(prod_costs, nonprod_costs)):
            if prod > 0:
                ax.text(prod / 2, i, f'${prod:,.0f}', ha='center', va='center', 
                       color='white', fontweight='bold', fontsize=8)
            if nonprod > 0:
                ax.text(prod + nonprod / 2, i, f'${nonprod:,.0f}', ha='center', va='center', 
                       color='white', fontweight='bold', fontsize=8)
        
        # Add legend with explicit handles
        ax.legend([prod_bars, nonprod_bars], ['PROD', 'NON-PROD'])
        
        plt.tight_layout()
        return encode_figure_to_base64(fig)
    
    except Exception as e:
        logger.error(f"Error creating product breakdown chart: {e}")
        return ""