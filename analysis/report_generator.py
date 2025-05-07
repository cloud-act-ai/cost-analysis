"""
Report generator for FinOps analysis.
"""
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import jinja2
from google.cloud import bigquery

from analysis.comparisons import compare_days, compare_weeks, compare_months, compare_years
from analysis.trends import get_daily_trend, get_monthly_trend, get_product_team_trend
from analysis.visualizations import (
    create_trend_chart, 
    create_comparison_chart, 
    create_team_comparison_chart,
    create_forecast_chart
)

def generate_report(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    table: str,
    output_dir: str = "output",
    report_type: str = "html",
    comparison_type: str = "day",
    trend_days: int = 30,
    forecast_days: int = 30,
    top_teams: int = 5
) -> str:
    """
    Generate a comprehensive FinOps report.
    
    Args:
        client: BigQuery client
        project_id: BigQuery project ID
        dataset: BigQuery dataset
        table: BigQuery table
        output_dir: Directory to store the report
        report_type: Report type (html or txt)
        comparison_type: Type of comparison (day, week, month, year)
        trend_days: Number of days to include in trend
        forecast_days: Number of days to forecast
        top_teams: Number of top teams to include
        
    Returns:
        Path to the generated report
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get current date for report filename and report date
    now = datetime.now()
    current_month = now.strftime("%b")
    current_fy = f"FY{now.year + 1}" if now.month >= 7 else f"FY{now.year}"
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # Generate comparison data based on type
    comparison_data = {}
    if comparison_type == "day":
        comparison_data = compare_days(client, project_id, dataset, table)
    elif comparison_type == "week":
        comparison_data = compare_weeks(client, project_id, dataset, table)
    elif comparison_type == "month":
        # Get current and previous month
        today = datetime.now()
        current_month = today.month
        current_year = today.year
        
        if current_month > 1:
            prev_month = current_month - 1
            prev_year = current_year
        else:
            prev_month = 12
            prev_year = current_year - 1
            
        comparison_data = compare_months(
            client, project_id, dataset, table,
            month1=prev_month, year1=prev_year,
            month2=current_month, year2=current_year
        )
    elif comparison_type == "year":
        # Get current and previous year
        today = datetime.now()
        current_year = today.year
        prev_year = current_year - 1
        
        comparison_data = compare_years(
            client, project_id, dataset, table,
            year1=prev_year, year2=current_year
        )
    
    # Generate trend data
    end_date = now.strftime("%Y-%m-%d")
    start_date_trend = (now - pd.Timedelta(days=trend_days)).strftime("%Y-%m-%d")
    
    # Get daily trends with environment breakdown
    daily_trend = get_daily_trend(
        client, project_id, dataset, table,
        start_date=start_date_trend,
        end_date=end_date,
        group_by="environment",
        forecast_days=forecast_days
    )
    
    # Get monthly trends
    # Extract year and month from start and end dates
    start_date_obj = datetime.strptime(start_date_trend, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    
    monthly_trend = get_monthly_trend(
        client, project_id, dataset, table,
        start_year=start_date_obj.year,
        start_month=start_date_obj.month,
        end_year=end_date_obj.year,
        end_month=end_date_obj.month,
        group_by="environment"
    )
    
    # Get product team trends
    team_trend = get_product_team_trend(
        client, project_id, dataset, table,
        start_date=start_date_trend,
        end_date=end_date,
        top_n=top_teams
    )
    
    # Generate charts
    comparison_chart = create_comparison_chart(
        comparison_data, 
        title=f"{comparison_type.capitalize()} Cost Comparison"
    )
    
    daily_trend_chart = create_trend_chart(
        daily_trend,
        title="Daily Cost Trend by Environment"
    )
    
    monthly_trend_chart = create_trend_chart(
        monthly_trend,
        title="Monthly Cost Trend by Environment"
    )
    
    team_chart = create_team_comparison_chart(
        team_trend,
        title="Top Product Pillar Teams by Cost"
    )
    
    # Generate a forecast chart from the daily trend data if forecast was requested
    forecast_chart = None
    if forecast_days > 0:
        forecast_chart = create_forecast_chart(
            {"data": daily_trend.get("trend", [])},
            title="Cost Forecast (Next 30 Days)"
        )
    
    # Prepare data for the report template
    report_data = {
        "report_date": now.strftime("%Y-%m-%d"),
        "comparison_type": comparison_type,
        "comparison_data": comparison_data,
        "daily_trend": daily_trend,
        "monthly_trend": monthly_trend,
        "team_trend": team_trend,
        "comparison_chart": comparison_chart,
        "daily_trend_chart": daily_trend_chart,
        "monthly_trend_chart": monthly_trend_chart,
        "team_chart": team_chart,
        "forecast_chart": forecast_chart,
        "has_forecast": forecast_days > 0
    }
    
    # Generate the report
    if report_type == "html":
        # Load template from template directory
        template_loader = jinja2.FileSystemLoader(searchpath="templates")
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template("report_template.html")
        
        # Render the template with the data
        output = template.render(**report_data)
        
        # Write to file
        report_filename = f"env_analysis_report_month_{current_month}_{current_fy}_{timestamp}.html"
        report_path = os.path.join(output_dir, report_filename)
        with open(report_path, 'w') as f:
            f.write(output)
    else:
        # Simple text report
        output = f"""
        FinOps Analysis Report - {now.strftime("%Y-%m-%d")}
        
        {comparison_type.capitalize()} Cost Comparison:
        {"=" * 40}
        Period 1: {comparison_data.get('period1', 'Previous period')}
        Period 2: {comparison_data.get('period2', 'Current period')}
        
        Total Cost Period 1: ${comparison_data.get('total1', 0):,.2f}
        Total Cost Period 2: ${comparison_data.get('total2', 0):,.2f}
        
        Percent Change: {comparison_data.get('percent_change', 0):+.2f}%
        
        Environment Breakdown:
        {"=" * 40}
        Production:
            Period 1: ${comparison_data.get('prod_cost1', 0):,.2f}
            Period 2: ${comparison_data.get('prod_cost2', 0):,.2f}
            Change: {comparison_data.get('prod_percent_change', 0):+.2f}%
            
        Non-Production:
            Period 1: ${comparison_data.get('nonprod_cost1', 0):,.2f}
            Period 2: ${comparison_data.get('nonprod_cost2', 0):,.2f}
            Change: {comparison_data.get('nonprod_percent_change', 0):+.2f}%
        
        Top Product Pillar Teams:
        {"=" * 40}
        """
        
        # Add team data
        for team in team_trend.get('teams', []):
            output += f"""
        {team['name']}: ${team['total_cost']:,.2f}
            """
        
        # Write to file
        report_filename = f"env_analysis_report_month_{current_month}_{current_fy}_{timestamp}.txt"
        report_path = os.path.join(output_dir, report_filename)
        with open(report_path, 'w') as f:
            f.write(output)
    
    return report_path