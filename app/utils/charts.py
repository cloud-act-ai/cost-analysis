"""
Chart generation utilities for FinOps360 cost analysis dashboard.
"""
import logging
import base64
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
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
    Create a daily trend chart with both actual and average costs.
    
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
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No data available for trend chart', 
                   ha='center', va='center', fontsize=14)
            ax.set_title('Daily Cost vs. Average Baselines', fontsize=14)
            plt.tight_layout()
            return encode_figure_to_base64(fig)
            
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(10, 6))
        legend_handles = []
        legend_labels = []
        
        # Plot each environment type
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
            
            # Plot FY25 average (historical baseline)
            line2, = ax.plot(
                group['date'], 
                group['fy25_avg_daily_spend'], 
                linestyle='--',
                linewidth=1.5,
                color='gray' if env == 'PROD' else 'lightgreen'
            )
            legend_handles.append(line2)
            legend_labels.append(f"{env} FY25 Avg")
            
            # Plot YTD average (current baseline)
            line3, = ax.plot(
                group['date'], 
                group['fy26_ytd_avg_daily_spend'], 
                linestyle='-.',
                linewidth=1.5,
                color='blue' if env == 'PROD' else 'green'
            )
            legend_handles.append(line3)
            legend_labels.append(f"{env} FY26 YTD Avg")
                
        # Format the plot
        ax.set_title('Daily Cost vs. Average Baselines', fontsize=14)
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