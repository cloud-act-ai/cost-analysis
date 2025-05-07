"""
Utilities for generating BigQuery-based dashboards and reports.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from google.cloud import bigquery

# Configure logging
logger = logging.getLogger(__name__)

def create_report_directory():
    """Create directory for reports if it doesn't exist."""
    report_dir = os.path.join(os.getcwd(), 'reports')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    return report_dir

def run_dashboard_query(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    view_name: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 1000
) -> pd.DataFrame:
    """
    Run a query against a dashboard view.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        view_name: Name of the dashboard view to query
        filters: Optional dictionary of column:value pairs for filtering
        limit: Maximum number of rows to return
        
    Returns:
        DataFrame with query results
    """
    try:
        # Build the base query
        query = f"SELECT * FROM `{project_id}.{dataset}.{view_name}`"
        
        # Add filters if provided
        if filters:
            filter_clauses = []
            for column, value in filters.items():
                if isinstance(value, str):
                    filter_clauses.append(f"{column} = '{value}'")
                elif isinstance(value, (int, float)):
                    filter_clauses.append(f"{column} = {value}")
                elif isinstance(value, list):
                    if all(isinstance(v, str) for v in value):
                        values_str = "', '".join(value)
                        filter_clauses.append(f"{column} IN ('{values_str}')")
                    else:
                        values_str = ", ".join(str(v) for v in value)
                        filter_clauses.append(f"{column} IN ({values_str})")
                    
            if filter_clauses:
                query += " WHERE " + " AND ".join(filter_clauses)
        
        # Add limit
        query += f" LIMIT {limit}"
        
        # Execute query
        df = client.query(query).to_dataframe(create_bqstorage_client=True)
        
        # Convert date columns to datetime
        for col in df.columns:
            if col.lower() == 'date' or col.lower().endswith('_date'):
                if df[col].dtype == 'object':
                    df[col] = pd.to_datetime(df[col])
        
        return df
        
    except Exception as e:
        logger.error(f"Error running dashboard query: {e}")
        return pd.DataFrame()

def create_daily_cost_chart(
    df: pd.DataFrame,
    x_col: str = 'date',
    y_cols: List[str] = ['daily_cost', 'fy25_avg_daily_spend', 'fy26_ytd_avg_daily_spend'],
    group_col: Optional[str] = 'environment_type',
    title: str = 'Daily Cost vs. Historical Averages',
    output_path: Optional[str] = None
) -> str:
    """
    Create a chart comparing daily costs with historical averages.
    
    Args:
        df: DataFrame with cost data
        x_col: Column to use for x-axis (usually date)
        y_cols: List of columns to plot as lines
        group_col: Optional column to group by (e.g., environment_type)
        title: Chart title
        output_path: Optional path to save the chart (if None, auto-generated)
        
    Returns:
        Path to the saved chart file
    """
    try:
        # Set up plot style
        plt.style.use('ggplot')
        sns.set_palette("colorblind")
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot the data
        if group_col:
            # Multiple lines grouped by group_col
            for group_name, group_df in df.groupby(group_col):
                for y_col in y_cols:
                    ax.plot(
                        group_df[x_col], 
                        group_df[y_col], 
                        marker='o' if y_col == y_cols[0] else None,
                        linestyle='-' if y_col == y_cols[0] else '--',
                        linewidth=2 if y_col == y_cols[0] else 1.5,
                        label=f"{group_name} - {y_col.replace('_', ' ').title()}"
                    )
        else:
            # Simple line chart without grouping
            for y_col in y_cols:
                ax.plot(
                    df[x_col], 
                    df[y_col], 
                    marker='o' if y_col == y_cols[0] else None,
                    linestyle='-' if y_col == y_cols[0] else '--',
                    linewidth=2 if y_col == y_cols[0] else 1.5,
                    label=f"{y_col.replace('_', ' ').title()}"
                )
                
        # Format the plot
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cost ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format date labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        fig.autofmt_xdate()
        
        # Add legend
        ax.legend()
        
        # Create output directory if needed
        report_dir = create_report_directory()
        
        # Save the figure
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(report_dir, f"daily_cost_chart_{timestamp}.png")
            
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating daily cost chart: {e}")
        return "Error: Failed to create chart"

def create_forecast_chart(
    df: pd.DataFrame,
    x_col: str = 'date',
    actual_col: str = 'daily_cost',
    forecast_col: str = 'fy26_forecasted_avg_daily_spend',
    group_col: Optional[str] = 'environment_type',
    title: str = 'Cost Forecast Analysis',
    output_path: Optional[str] = None
) -> str:
    """
    Create a forecast chart comparing actual and forecasted costs.
    
    Args:
        df: DataFrame with cost data
        x_col: Column to use for x-axis (usually date)
        actual_col: Column with actual cost data
        forecast_col: Column with forecasted cost data
        group_col: Optional column to group by (e.g., environment_type)
        title: Chart title
        output_path: Optional path to save the chart (if None, auto-generated)
        
    Returns:
        Path to the saved chart file
    """
    try:
        # Set up plot style
        plt.style.use('ggplot')
        sns.set_palette("colorblind")
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot the data
        if group_col:
            # Multiple lines grouped by group_col
            for group_name, group_df in df.groupby(group_col):
                # Plot actual data
                ax.plot(
                    group_df[x_col], 
                    group_df[actual_col], 
                    marker='o',
                    linestyle='-',
                    linewidth=2,
                    label=f"{group_name} - Actual"
                )
                
                # Plot forecast data
                ax.plot(
                    group_df[x_col], 
                    group_df[forecast_col], 
                    marker=None,
                    linestyle='--',
                    linewidth=1.5,
                    label=f"{group_name} - Forecast"
                )
                
                # Add shaded area for forecast range (±10%)
                ax.fill_between(
                    group_df[x_col],
                    group_df[forecast_col] * 0.9,
                    group_df[forecast_col] * 1.1,
                    alpha=0.2,
                    label=f"{group_name} - Forecast Range (±10%)"
                )
        else:
            # Simple chart without grouping
            # Plot actual data
            ax.plot(
                df[x_col], 
                df[actual_col], 
                marker='o',
                linestyle='-',
                linewidth=2,
                label="Actual"
            )
            
            # Plot forecast data
            ax.plot(
                df[x_col], 
                df[forecast_col], 
                marker=None,
                linestyle='--',
                linewidth=1.5,
                label="Forecast"
            )
            
            # Add shaded area for forecast range (±10%)
            ax.fill_between(
                df[x_col],
                df[forecast_col] * 0.9,
                df[forecast_col] * 1.1,
                alpha=0.2,
                label="Forecast Range (±10%)"
            )
                
        # Format the plot
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cost ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format date labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        fig.autofmt_xdate()
        
        # Add legend
        ax.legend()
        
        # Create output directory if needed
        report_dir = create_report_directory()
        
        # Save the figure
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(report_dir, f"forecast_chart_{timestamp}.png")
            
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating forecast chart: {e}")
        return "Error: Failed to create chart"

def create_yoy_comparison_chart(
    df: pd.DataFrame,
    value_cols: List[str] = ['fy24_avg_daily_spend', 'fy25_avg_daily_spend', 'fy26_avg_daily_spend'],
    group_col: str = 'environment_type',
    title: str = 'Year-over-Year Cost Comparison',
    output_path: Optional[str] = None
) -> str:
    """
    Create a bar chart comparing costs across fiscal years.
    
    Args:
        df: DataFrame with cost data
        value_cols: List of columns with fiscal year data
        group_col: Column to group by (e.g., environment_type)
        title: Chart title
        output_path: Optional path to save the chart (if None, auto-generated)
        
    Returns:
        Path to the saved chart file
    """
    try:
        # Set up plot style
        plt.style.use('ggplot')
        sns.set_palette("colorblind")
        
        # Aggregate data by group
        grouped_df = df.groupby(group_col)[value_cols].mean().reset_index()
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Set up bar positions
        bar_width = 0.25
        index = range(len(grouped_df))
        
        # Plot bars for each fiscal year
        for i, col in enumerate(value_cols):
            position = [x + i * bar_width for x in index]
            bars = ax.bar(
                position, 
                grouped_df[col], 
                bar_width,
                label=col.replace('_', ' ').title()
            )
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height * 1.01,
                    f'${height:,.0f}',
                    ha='center', 
                    va='bottom',
                    fontsize=8
                )
                
        # Calculate year-over-year percent changes
        if len(value_cols) >= 2:
            for i in range(len(value_cols) - 1):
                current_col = value_cols[i+1]
                previous_col = value_cols[i]
                
                for j, row in grouped_df.iterrows():
                    current = row[current_col]
                    previous = row[previous_col]
                    
                    if previous > 0:
                        percent_change = ((current / previous) - 1) * 100
                        position = index[j] + (i + 0.5) * bar_width
                        color = 'red' if percent_change > 0 else 'green'
                        
                        ax.text(
                            position,
                            max(current, previous) * 1.05,
                            f"{percent_change:+.1f}%",
                            ha='center',
                            va='bottom',
                            color=color,
                            fontweight='bold',
                            fontsize=9
                        )
                
        # Format the plot
        ax.set_title(title, fontsize=14)
        ax.set_ylabel('Average Daily Cost ($)', fontsize=12)
        ax.set_xticks([x + bar_width for x in index])
        ax.set_xticklabels(grouped_df[group_col])
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add legend
        ax.legend()
        
        # Create output directory if needed
        report_dir = create_report_directory()
        
        # Save the figure
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(report_dir, f"yoy_comparison_chart_{timestamp}.png")
            
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating YoY comparison chart: {e}")
        return "Error: Failed to create chart"

def create_cost_breakdown_chart(
    df: pd.DataFrame,
    category_col: str = 'tr_product_pillar_team',
    value_col: str = 'detailed_cost',
    title: str = 'Cost Breakdown by Category',
    top_n: int = 10,
    output_path: Optional[str] = None
) -> str:
    """
    Create a pie or bar chart showing cost breakdown by category.
    
    Args:
        df: DataFrame with cost data
        category_col: Column to use for categories
        value_col: Column with cost values
        title: Chart title
        top_n: Number of top categories to include (others grouped as "Other")
        output_path: Optional path to save the chart (if None, auto-generated)
        
    Returns:
        Path to the saved chart file
    """
    try:
        # Set up plot style
        plt.style.use('ggplot')
        colors = sns.color_palette('colorblind', 10)
        
        # Aggregate data by category
        grouped_df = df.groupby(category_col)[value_col].sum().reset_index()
        
        # Sort and get top N categories
        grouped_df = grouped_df.sort_values(value_col, ascending=False)
        
        # Create a copy for the pie chart
        if len(grouped_df) > top_n:
            pie_df = pd.DataFrame()
            pie_df = pd.concat([
                grouped_df.head(top_n),
                pd.DataFrame({
                    category_col: ['Other'],
                    value_col: [grouped_df.iloc[top_n:][value_col].sum()]
                })
            ])
        else:
            pie_df = grouped_df.copy()
        
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
        
        # Plot pie chart
        wedges, texts, autotexts = ax1.pie(
            pie_df[value_col],
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )
        
        # Adjust text properties
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            
        # Add legend
        ax1.legend(
            wedges,
            pie_df[category_col],
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        
        # Plot horizontal bar chart (top 10 only)
        bar_df = grouped_df.head(top_n).copy()
        # Reverse order for better visual
        bar_df = bar_df.iloc[::-1].reset_index(drop=True)
        
        bars = ax2.barh(bar_df[category_col], bar_df[value_col], color=colors)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax2.text(
                width * 1.01,
                bar.get_y() + bar.get_height() / 2,
                f'${width:,.0f}',
                ha='left',
                va='center',
                fontsize=9
            )
            
        # Calculate percentage of total
        total_cost = grouped_df[value_col].sum()
        bar_df['percent'] = bar_df[value_col] / total_cost * 100
        
        # Add percentage labels
        for i, row in bar_df.iterrows():
            ax2.text(
                row[value_col] * 0.02,  # Small offset from start of bar
                i,
                f"{row['percent']:.1f}%",
                ha='left',
                va='center',
                color='white',
                fontweight='bold',
                fontsize=9
            )
            
        # Format the bar chart
        ax2.set_title(f"Top {top_n} {category_col.replace('_', ' ').title()}", fontsize=12)
        ax2.set_xlabel('Cost ($)', fontsize=10)
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Set overall title
        fig.suptitle(title, fontsize=14)
        
        # Create output directory if needed
        report_dir = create_report_directory()
        
        # Save the figure
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(report_dir, f"cost_breakdown_chart_{timestamp}.png")
            
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for suptitle
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating cost breakdown chart: {e}")
        return "Error: Failed to create chart"

def generate_dashboard(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    environment_filter: Optional[str] = None,
    cto_filter: Optional[str] = None,
    date_range: Optional[Tuple[str, str]] = None,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate a complete dashboard with multiple charts.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        environment_filter: Optional environment to filter by
        cto_filter: Optional CTO to filter by
        date_range: Optional (start_date, end_date) tuple
        output_dir: Optional directory to save charts
        
    Returns:
        Dictionary of chart names and file paths
    """
    try:
        # Create output directory if needed
        if output_dir:
            report_dir = output_dir
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
        else:
            report_dir = create_report_directory()
            
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Charts to generate
        charts = {}
        
        # 1. Daily Cost Trend Chart
        # Prepare filters
        filters = {}
        if environment_filter:
            filters['environment_type'] = environment_filter
        if cto_filter:
            filters['cto'] = cto_filter
        if date_range:
            # Not used in the filter but will be used to filter DataFrame
            pass
            
        # Query data
        daily_df = run_dashboard_query(
            client, project_id, dataset, 'avg_daily_cost_table',
            filters=filters
        )
        
        # Apply date filter if provided
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            daily_df = daily_df[(daily_df['date'] >= start_date) & (daily_df['date'] <= end_date)]
            
        # Sort by date
        daily_df = daily_df.sort_values('date')
        
        # Create chart
        if not daily_df.empty:
            # Create chart title
            title_parts = ['Daily Cost Trend']
            if environment_filter:
                title_parts.append(f"for {environment_filter}")
            if cto_filter:
                title_parts.append(f"({cto_filter})")
                
            daily_chart_path = create_daily_cost_chart(
                daily_df,
                title=' '.join(title_parts),
                output_path=os.path.join(report_dir, f"daily_cost_trend_{timestamp}.png")
            )
            charts['daily_cost_trend'] = daily_chart_path
            
            # Also create a forecast chart
            forecast_chart_path = create_forecast_chart(
                daily_df,
                title=f"Cost Forecast {' '.join(title_parts[1:])}",
                output_path=os.path.join(report_dir, f"cost_forecast_{timestamp}.png")
            )
            charts['cost_forecast'] = forecast_chart_path
        
        # 2. YoY Comparison Chart
        # Query data (use environment_breakdown view for better aggregation)
        yoy_filters = {}
        if environment_filter:
            yoy_filters['environment_type'] = environment_filter
            
        yoy_df = run_dashboard_query(
            client, project_id, dataset, 'environment_breakdown',
            filters=yoy_filters
        )
        
        # Create chart
        if not yoy_df.empty:
            # Create a title
            title_parts = ['Year-over-Year Cost Comparison']
            if environment_filter:
                title_parts.append(f"for {environment_filter}")
                
            yoy_chart_path = create_yoy_comparison_chart(
                yoy_df,
                title=' '.join(title_parts),
                output_path=os.path.join(report_dir, f"yoy_comparison_{timestamp}.png")
            )
            charts['yoy_comparison'] = yoy_chart_path
        
        # 3. Cost Breakdown Chart
        # Query data from detailed breakdown view
        breakdown_filters = {}
        if environment_filter:
            breakdown_filters['environment_type'] = environment_filter
        if cto_filter:
            breakdown_filters['cto'] = cto_filter
            
        breakdown_df = run_dashboard_query(
            client, project_id, dataset, 'detailed_cost_categories',
            filters=breakdown_filters
        )
        
        # Create chart
        if not breakdown_df.empty:
            # Create chart for product pillar teams
            title_parts = ['Cost Breakdown by Product Pillar Team']
            if environment_filter:
                title_parts.append(f"for {environment_filter}")
            if cto_filter:
                title_parts.append(f"({cto_filter})")
                
            pillar_chart_path = create_cost_breakdown_chart(
                breakdown_df,
                category_col='tr_product_pillar_team',
                title=' '.join(title_parts),
                output_path=os.path.join(report_dir, f"pillar_breakdown_{timestamp}.png")
            )
            charts['pillar_breakdown'] = pillar_chart_path
            
            # Create chart for cloud providers
            title_parts[0] = 'Cost Breakdown by Cloud Provider'
            cloud_chart_path = create_cost_breakdown_chart(
                breakdown_df,
                category_col='cloud',
                title=' '.join(title_parts),
                output_path=os.path.join(report_dir, f"cloud_breakdown_{timestamp}.png")
            )
            charts['cloud_breakdown'] = cloud_chart_path
            
            # Create chart for managed services
            title_parts[0] = 'Cost Breakdown by Managed Service'
            service_chart_path = create_cost_breakdown_chart(
                breakdown_df,
                category_col='managed_service',
                title=' '.join(title_parts),
                output_path=os.path.join(report_dir, f"service_breakdown_{timestamp}.png")
            )
            charts['service_breakdown'] = service_chart_path
        
        return charts
    
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        return {"error": str(e)}