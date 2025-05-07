#!/usr/bin/env python3
"""
Script to generate an HTML dashboard report with both production and non-production cost data.
"""
import os
import sys
import argparse
import jinja2
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import base64
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from google.cloud import bigquery
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from common.finops_config import load_config

def encode_figure_to_base64(fig):
    """Encode a matplotlib figure to base64 for embedding in HTML."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def run_query(client, query):
    """Run a BigQuery query and return results as a DataFrame."""
    try:
        return client.query(query).to_dataframe(create_bqstorage_client=True)
    except Exception as e:
        logger.error(f"Error running query: {e}")
        logger.error(f"Query: {query}")
        return pd.DataFrame()

def get_ytd_costs(client, project_id, dataset, table):
    """Get year-to-date costs for production and non-production."""
    query = f"""
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS ytd_cost,
        COUNT(DISTINCT date) AS days
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3
    GROUP BY environment_type
    """
    return run_query(client, query)

def get_fy26_costs(client, project_id, dataset, table):
    """Get projected FY26 costs for production and non-production."""
    query = f"""
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost,
        COUNT(DISTINCT date) AS days
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '2025-02-01' AND '2026-01-31'
    GROUP BY environment_type
    """
    return run_query(client, query)

def get_fy25_costs(client, project_id, dataset, table):
    """Get FY25 costs for year-over-year comparison."""
    query = f"""
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost,
        COUNT(DISTINCT date) AS days
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '2024-02-01' AND '2025-01-31'
    GROUP BY environment_type
    """
    return run_query(client, query)

def get_recent_comparisons(client, project_id, dataset, table):
    """Get recent day, week, and month comparisons."""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)
    
    # Day-to-day comparison (4 days ago vs 5 days ago)
    day4 = today - timedelta(days=4)
    day5 = today - timedelta(days=5)
    
    day_query = f"""
    WITH day4 AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date = '{day4}'
        GROUP BY environment_type
    ),
    day5 AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date = '{day5}'
        GROUP BY environment_type
    )
    SELECT
        d4.environment_type,
        d4.total_cost AS day4_cost,
        d5.total_cost AS day5_cost,
        (d4.total_cost - d5.total_cost) / NULLIF(d5.total_cost, 0) * 100 AS percent_change
    FROM day4 d4
    JOIN day5 d5 ON d4.environment_type = d5.environment_type
    """
    day_comparison = run_query(client, day_query)
    
    # Week-to-week comparison
    this_week_start = today - timedelta(days=today.weekday() + 7)  # Last week's start
    this_week_end = this_week_start + timedelta(days=6)
    prev_week_start = this_week_start - timedelta(days=7)
    prev_week_end = prev_week_start + timedelta(days=6)
    
    week_query = f"""
    WITH this_week AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{this_week_start}' AND '{this_week_end}'
        GROUP BY environment_type
    ),
    prev_week AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{prev_week_start}' AND '{prev_week_end}'
        GROUP BY environment_type
    )
    SELECT
        tw.environment_type,
        tw.total_cost AS this_week_cost,
        pw.total_cost AS prev_week_cost,
        (tw.total_cost - pw.total_cost) / NULLIF(pw.total_cost, 0) * 100 AS percent_change
    FROM this_week tw
    JOIN prev_week pw ON tw.environment_type = pw.environment_type
    """
    week_comparison = run_query(client, week_query)
    
    # Month-to-month comparison
    this_month = today.replace(day=1)
    prev_month = (this_month.replace(day=1) - timedelta(days=1)).replace(day=1)
    this_month_end = today
    days_in_prev_month = (this_month - timedelta(days=1)).day
    prev_month_end = prev_month.replace(day=min(this_month_end.day, days_in_prev_month))
    
    month_query = f"""
    WITH this_month AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{this_month}' AND '{this_month_end}'
        GROUP BY environment_type
    ),
    prev_month AS (
        SELECT
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment_type,
            SUM(cost) AS total_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '{prev_month}' AND '{prev_month_end}'
        GROUP BY environment_type
    )
    SELECT
        tm.environment_type,
        tm.total_cost AS this_month_cost,
        pm.total_cost AS prev_month_cost,
        (tm.total_cost - pm.total_cost) / NULLIF(pm.total_cost, 0) * 100 AS percent_change
    FROM this_month tm
    JOIN prev_month pm ON tm.environment_type = pm.environment_type
    """
    month_comparison = run_query(client, month_query)
    
    return day_comparison, week_comparison, month_comparison

def get_product_costs(client, project_id, dataset, table):
    """Get costs by product ID with prod/nonprod breakdown."""
    query = f"""
    WITH product_costs AS (
        SELECT
            tr_product_id AS product_id,
            tr_product AS product_name,
            tr_product_pillar_team AS pillar_team,
            CASE 
                WHEN environment LIKE '%PROD%' THEN 'PROD'
                ELSE 'NON-PROD'
            END AS environment,
            SUM(cost) AS ytd_cost
        FROM `{project_id}.{dataset}.{table}`
        WHERE date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3
        GROUP BY product_id, product_name, pillar_team, environment
    ),
    prod_costs AS (
        SELECT
            product_id,
            product_name,
            pillar_team,
            ytd_cost AS prod_ytd_cost
        FROM product_costs
        WHERE environment = 'PROD'
    ),
    nonprod_costs AS (
        SELECT
            product_id,
            product_name,
            pillar_team,
            ytd_cost AS nonprod_ytd_cost
        FROM product_costs
        WHERE environment = 'NON-PROD'
    ),
    combined_costs AS (
        SELECT
            COALESCE(p.product_id, np.product_id) AS product_id,
            COALESCE(p.product_name, np.product_name) AS product_name,
            COALESCE(p.pillar_team, np.pillar_team) AS pillar_team,
            COALESCE(p.prod_ytd_cost, 0) AS prod_ytd_cost,
            COALESCE(np.nonprod_ytd_cost, 0) AS nonprod_ytd_cost,
            COALESCE(p.prod_ytd_cost, 0) + COALESCE(np.nonprod_ytd_cost, 0) AS total_ytd_cost
        FROM prod_costs p
        FULL OUTER JOIN nonprod_costs np ON p.product_id = np.product_id
    )
    SELECT
        product_id,
        product_name,
        pillar_team,
        prod_ytd_cost,
        nonprod_ytd_cost,
        total_ytd_cost,
        CASE 
            WHEN total_ytd_cost > 0 THEN (nonprod_ytd_cost / total_ytd_cost) * 100
            ELSE 0
        END AS nonprod_percentage
    FROM combined_costs
    WHERE total_ytd_cost > 0
    ORDER BY total_ytd_cost DESC
    LIMIT 50
    """
    return run_query(client, query)

def get_daily_trend_data(client, project_id, dataset, avg_table, days=90):
    """Get daily trend data from avg_daily_cost_table."""
    end_date = datetime.now().date() - timedelta(days=3)  # Latest available data
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT
        date,
        environment_type,
        daily_cost,
        fy25_avg_daily_spend,
        fy26_ytd_avg_daily_spend,
        fy26_forecasted_avg_daily_spend
    FROM `{project_id}.{dataset}.{avg_table}`
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date
    """
    return run_query(client, query)

def create_daily_trend_chart(df):
    """Create a daily trend chart with both actual and average costs."""
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

def create_forecast_chart(df):
    """Create a chart showing actual vs forecasted costs from avg_daily_cost_table."""
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

def create_environment_breakdown_chart(prod_df, nonprod_df):
    """Create a chart showing environment cost breakdown."""
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

def create_product_breakdown_chart(product_df, top_n=10):
    """Create a chart showing top products by cost."""
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

def generate_html_report(
    client,
    project_id,
    dataset,
    cost_table,
    avg_table,
    template_path,
    output_path
):
    """Generate a comprehensive HTML report."""
    try:
        # Get YTD costs
        ytd_costs = get_ytd_costs(client, project_id, dataset, cost_table)
        prod_ytd = ytd_costs[ytd_costs['environment_type'] == 'PROD']
        nonprod_ytd = ytd_costs[ytd_costs['environment_type'] == 'NON-PROD']
        
        # Get FY26 costs
        fy26_costs = get_fy26_costs(client, project_id, dataset, cost_table)
        prod_fy26 = fy26_costs[fy26_costs['environment_type'] == 'PROD']
        nonprod_fy26 = fy26_costs[fy26_costs['environment_type'] == 'NON-PROD']
        
        # Get FY25 costs for comparison
        fy25_costs = get_fy25_costs(client, project_id, dataset, cost_table)
        prod_fy25 = fy25_costs[fy25_costs['environment_type'] == 'PROD']
        nonprod_fy25 = fy25_costs[fy25_costs['environment_type'] == 'NON-PROD']
        
        # Calculate YoY percentages
        prod_ytd_percent = 0
        if not prod_fy25.empty and not prod_ytd.empty and prod_fy25['total_cost'].iloc[0] > 0:
            # Annualize YTD for fair comparison
            prod_ytd_annualized = prod_ytd['ytd_cost'].iloc[0] * (365 / prod_ytd['days'].iloc[0])
            prod_ytd_percent = ((prod_ytd_annualized / prod_fy25['total_cost'].iloc[0]) - 1) * 100
            
        nonprod_ytd_percent = 0
        if not nonprod_fy25.empty and not nonprod_ytd.empty and nonprod_fy25['total_cost'].iloc[0] > 0:
            # Annualize YTD for fair comparison
            nonprod_ytd_annualized = nonprod_ytd['ytd_cost'].iloc[0] * (365 / nonprod_ytd['days'].iloc[0])
            nonprod_ytd_percent = ((nonprod_ytd_annualized / nonprod_fy25['total_cost'].iloc[0]) - 1) * 100
        
        # Calculate total FY26 cost
        total_fy26_cost = fy26_costs['total_cost'].sum()
        total_fy25_cost = fy25_costs['total_cost'].sum()
        fy26_percent = ((total_fy26_cost / total_fy25_cost) - 1) * 100 if total_fy25_cost > 0 else 0
        
        # Calculate nonprod percentage
        total_ytd = ytd_costs['ytd_cost'].sum()
        nonprod_percentage = (nonprod_ytd['ytd_cost'].iloc[0] / total_ytd * 100) if not nonprod_ytd.empty and total_ytd > 0 else 0
        
        # Get month-to-month nonprod percentage for comparison
        day_comparison, week_comparison, month_comparison = get_recent_comparisons(client, project_id, dataset, cost_table)
        
        # Calculate nonprod percentage change vs last month
        this_month_nonprod = month_comparison[month_comparison['environment_type'] == 'NON-PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values else 0
        this_month_total = month_comparison['this_month_cost'].sum() if not month_comparison.empty else 0
        
        prev_month_nonprod = month_comparison[month_comparison['environment_type'] == 'NON-PROD']['prev_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values else 0
        prev_month_total = month_comparison['prev_month_cost'].sum() if not month_comparison.empty else 0
        
        this_month_percent = (this_month_nonprod / this_month_total * 100) if this_month_total > 0 else 0
        prev_month_percent = (prev_month_nonprod / prev_month_total * 100) if prev_month_total > 0 else 0
        nonprod_percentage_change = this_month_percent - prev_month_percent
        
        # Get product costs
        product_costs = get_product_costs(client, project_id, dataset, cost_table)
        
        # Prepare product cost table data
        product_cost_table = []
        for _, row in product_costs.iterrows():
            product_cost_table.append({
                'product_id': row['product_id'],
                'product_name': row['product_name'],
                'pillar_team': row['pillar_team'],
                'prod_ytd_cost': row['prod_ytd_cost'],
                'nonprod_ytd_cost': row['nonprod_ytd_cost'],
                'total_ytd_cost': row['total_ytd_cost'],
                'nonprod_percentage': row['nonprod_percentage']
            })
        
        # Get data for charts from avg_daily_cost_table
        daily_trend_data = get_daily_trend_data(client, project_id, dataset, avg_table)
        
        # Create charts
        daily_trend_chart = create_daily_trend_chart(daily_trend_data)
        forecast_chart = create_forecast_chart(daily_trend_data)
        env_breakdown_chart = create_environment_breakdown_chart(prod_ytd, nonprod_ytd)
        product_breakdown_chart = create_product_breakdown_chart(product_costs)
        
        # Load Jinja2 template
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        template = env.get_template(template_file)
        
        # Prepare template data
        template_data = {
            'report_start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'report_end_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'report_generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # Scorecard data
            'prod_ytd_cost': prod_ytd['ytd_cost'].iloc[0] if not prod_ytd.empty else 0,
            'nonprod_ytd_cost': nonprod_ytd['ytd_cost'].iloc[0] if not nonprod_ytd.empty else 0,
            'total_fy26_cost': total_fy26_cost,
            'prod_ytd_percent': prod_ytd_percent,
            'nonprod_ytd_percent': nonprod_ytd_percent,
            'fy26_percent': fy26_percent,
            'nonprod_percentage': nonprod_percentage,
            'nonprod_percentage_change': nonprod_percentage_change,
            
            # Recent comparisons
            'day_prod_cost': day_comparison[day_comparison['environment_type'] == 'PROD']['day4_cost'].iloc[0] if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values else 0,
            'day_nonprod_cost': day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day4_cost'].iloc[0] if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values else 0,
            'day_prod_percent': day_comparison[day_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values else 0,
            'day_nonprod_percent': day_comparison[day_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values else 0,
            
            'week_prod_cost': week_comparison[week_comparison['environment_type'] == 'PROD']['this_week_cost'].iloc[0] if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values else 0,
            'week_nonprod_cost': week_comparison[week_comparison['environment_type'] == 'NON-PROD']['this_week_cost'].iloc[0] if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values else 0,
            'week_prod_percent': week_comparison[week_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values else 0,
            'week_nonprod_percent': week_comparison[week_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values else 0,
            
            'month_prod_cost': month_comparison[month_comparison['environment_type'] == 'PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values else 0,
            'month_nonprod_cost': month_comparison[month_comparison['environment_type'] == 'NON-PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values else 0,
            'month_prod_percent': month_comparison[month_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values else 0,
            'month_nonprod_percent': month_comparison[month_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values else 0,
            
            # Charts
            'daily_trend_chart': daily_trend_chart,
            'forecast_chart': forecast_chart,
            'env_breakdown_chart': env_breakdown_chart,
            'product_breakdown_chart': product_breakdown_chart,
            
            # Tables
            'product_cost_table': product_cost_table
        }
        
        # Render template and save to file
        html_output = template.render(**template_data)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
            
        logger.info(f"HTML report generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")
        raise

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate FinOps HTML dashboard")
    
    parser.add_argument('--output', type=str, default='reports/finops_dashboard.html',
                       help="Output HTML file path (default: reports/finops_dashboard.html)")
    parser.add_argument('--config', type=str, default='config.yaml',
                       help="Path to config file (default: config.yaml)")
    parser.add_argument('--template', type=str, default='templates/dashboard_template.html',
                       help="Path to HTML template (default: templates/dashboard_template.html)")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Load configuration
        config = load_config(args.config)
        
        # Validate BigQuery configuration
        if not config.use_bigquery:
            logger.error("BigQuery is not enabled in the configuration.")
            sys.exit(1)
        
        # Set up BigQuery client
        credentials_path = config.get('bigquery_credentials')
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
        client = bigquery.Client(project=config.bigquery_project_id)
        
        # Generate HTML report
        report_path = generate_html_report(
            client=client,
            project_id=config.bigquery_project_id,
            dataset=config.bigquery_dataset,
            cost_table=config.bigquery_table,
            avg_table=config.get('avg_table', 'avg_daily_cost_table'),
            template_path=args.template,
            output_path=args.output
        )
        
        # Open the report if in a desktop environment
        if os.name == 'posix':  # macOS or Linux
            os.system(f"open {report_path}")
        elif os.name == 'nt':   # Windows
            os.system(f"start {report_path}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()