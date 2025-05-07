"""
Dashboard generation for FinOps360 cost analysis.
"""
import os
import logging
import jinja2
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List, Tuple

import pandas as pd
from google.cloud import bigquery

from app.utils.config import FinOpsConfig
from app.utils.charts import (
    create_daily_trend_chart,
    create_forecast_chart,
    create_environment_breakdown_chart,
    create_product_breakdown_chart
)

# Try to import interactive charts, but don't fail if plotly is not installed
try:
    from app.utils.interactive_charts import (
        create_interactive_daily_trend_chart,
        create_interactive_product_breakdown_chart,
        create_interactive_environment_breakdown_chart,
        get_project_dataset_config
    )
    has_interactive_charts = True
except ImportError:
    # Create dummy functions if plotly is not available
    def create_interactive_daily_trend_chart(*args, **kwargs):
        return "{}"
    def create_interactive_product_breakdown_chart(*args, **kwargs):
        return "{}"
    def create_interactive_environment_breakdown_chart(*args, **kwargs):
        return "{}"
    def get_project_dataset_config(*args, **kwargs):
        return {}
    has_interactive_charts = False
from app.data_access import (
    get_ytd_costs,
    get_fy26_costs,
    get_fy25_costs,
    get_recent_comparisons, 
    get_product_costs,
    get_daily_trend_data
)

# Import sample data for when BigQuery is not available
from app.utils.sample_data import (
    create_sample_ytd_costs,
    create_sample_fy26_costs,
    create_sample_fy25_costs,
    create_sample_day_comparison,
    create_sample_week_comparison,
    create_sample_month_comparison,
    create_sample_product_costs,
    create_sample_daily_trend_data
)

logger = logging.getLogger(__name__)

def generate_html_report(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    cost_table: str,
    avg_table: str,
    template_path: str,
    output_path: str,
    use_bigquery: bool = True,
    use_interactive_charts: bool = True
) -> str:
    """
    Generate a comprehensive HTML report.
    
    Args:
        client: BigQuery client
        project_id: Google Cloud project ID
        dataset: BigQuery dataset
        cost_table: Cost analysis table name
        avg_table: Average daily cost table name
        template_path: Path to HTML template
        output_path: Path to save the generated report
        use_bigquery: Whether to use BigQuery or sample data
        use_interactive_charts: Whether to generate interactive charts
        
    Returns:
        Path to the generated HTML report
    """
    try:
        # Decide whether to use BigQuery data or sample data
        if use_bigquery:
            try:
                # Get data from BigQuery
                ytd_costs = get_ytd_costs(client, project_id, dataset, cost_table)
                fy26_costs = get_fy26_costs(client, project_id, dataset, cost_table)
                fy25_costs = get_fy25_costs(client, project_id, dataset, cost_table)
                day_comparison, week_comparison, month_comparison = get_recent_comparisons(client, project_id, dataset, cost_table)
                product_costs = get_product_costs(client, project_id, dataset, cost_table)
                daily_trend_data = get_daily_trend_data(client, project_id, dataset, avg_table)
                logger.info("Successfully retrieved data from BigQuery")
            except Exception as e:
                logger.warning(f"Error retrieving data from BigQuery: {e}. Using sample data instead.")
                use_bigquery = False
        
        # Use sample data if BigQuery is disabled or had an error
        if not use_bigquery:
            logger.info("Using sample data for dashboard generation")
            ytd_costs = create_sample_ytd_costs()
            fy26_costs = create_sample_fy26_costs()
            fy25_costs = create_sample_fy25_costs()
            day_comparison = create_sample_day_comparison()
            week_comparison = create_sample_week_comparison()
            month_comparison = create_sample_month_comparison()
            product_costs = create_sample_product_costs()
            daily_trend_data = create_sample_daily_trend_data()
        
        # Extract and process data (same regardless of source)
        prod_ytd = ytd_costs[ytd_costs['environment_type'] == 'PROD'] if not ytd_costs.empty and 'PROD' in ytd_costs['environment_type'].values else pd.DataFrame()
        nonprod_ytd = ytd_costs[ytd_costs['environment_type'] == 'NON-PROD'] if not ytd_costs.empty and 'NON-PROD' in ytd_costs['environment_type'].values else pd.DataFrame()
        
        prod_fy26 = fy26_costs[fy26_costs['environment_type'] == 'PROD'] if not fy26_costs.empty and 'PROD' in fy26_costs['environment_type'].values else pd.DataFrame()
        nonprod_fy26 = fy26_costs[fy26_costs['environment_type'] == 'NON-PROD'] if not fy26_costs.empty and 'NON-PROD' in fy26_costs['environment_type'].values else pd.DataFrame()
        
        prod_fy25 = fy25_costs[fy25_costs['environment_type'] == 'PROD'] if not fy25_costs.empty and 'PROD' in fy25_costs['environment_type'].values else pd.DataFrame()
        nonprod_fy25 = fy25_costs[fy25_costs['environment_type'] == 'NON-PROD'] if not fy25_costs.empty and 'NON-PROD' in fy25_costs['environment_type'].values else pd.DataFrame()
        
        # Calculate YoY percentages
        prod_ytd_percent = 0
        if not prod_fy25.empty and not prod_ytd.empty and 'total_cost' in prod_fy25.columns and prod_fy25['total_cost'].iloc[0] > 0:
            # Annualize YTD for fair comparison
            prod_ytd_annualized = prod_ytd['ytd_cost'].iloc[0] * (365 / prod_ytd['days'].iloc[0])
            prod_ytd_percent = ((prod_ytd_annualized / prod_fy25['total_cost'].iloc[0]) - 1) * 100
            
        nonprod_ytd_percent = 0
        if not nonprod_fy25.empty and not nonprod_ytd.empty and 'total_cost' in nonprod_fy25.columns and nonprod_fy25['total_cost'].iloc[0] > 0:
            # Annualize YTD for fair comparison
            nonprod_ytd_annualized = nonprod_ytd['ytd_cost'].iloc[0] * (365 / nonprod_ytd['days'].iloc[0])
            nonprod_ytd_percent = ((nonprod_ytd_annualized / nonprod_fy25['total_cost'].iloc[0]) - 1) * 100
        
        # Calculate total FY26 cost
        total_fy26_cost = fy26_costs['total_cost'].sum() if not fy26_costs.empty and 'total_cost' in fy26_costs.columns else 0
        total_fy25_cost = fy25_costs['total_cost'].sum() if not fy25_costs.empty and 'total_cost' in fy25_costs.columns else 0
        fy26_percent = ((total_fy26_cost / total_fy25_cost) - 1) * 100 if total_fy25_cost > 0 else 0
        
        # Calculate nonprod percentage
        total_ytd = ytd_costs['ytd_cost'].sum() if not ytd_costs.empty and 'ytd_cost' in ytd_costs.columns else 0
        nonprod_percentage = (nonprod_ytd['ytd_cost'].iloc[0] / total_ytd * 100) if not nonprod_ytd.empty and 'ytd_cost' in nonprod_ytd.columns and total_ytd > 0 else 0
        
        # Calculate nonprod percentage change vs last month
        this_month_nonprod = month_comparison[month_comparison['environment_type'] == 'NON-PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and 'this_month_cost' in month_comparison.columns else 0
        this_month_total = month_comparison['this_month_cost'].sum() if not month_comparison.empty and 'this_month_cost' in month_comparison.columns else 0
        
        prev_month_nonprod = month_comparison[month_comparison['environment_type'] == 'NON-PROD']['prev_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and 'prev_month_cost' in month_comparison.columns else 0
        prev_month_total = month_comparison['prev_month_cost'].sum() if not month_comparison.empty and 'prev_month_cost' in month_comparison.columns else 0
        
        this_month_percent = (this_month_nonprod / this_month_total * 100) if this_month_total > 0 else 0
        prev_month_percent = (prev_month_nonprod / prev_month_total * 100) if prev_month_total > 0 else 0
        nonprod_percentage_change = this_month_percent - prev_month_percent
        
        # Prepare product cost table data
        product_cost_table = []
        for _, row in product_costs.iterrows():
            product_cost_table.append({
                'product_id': row['product_id'] if 'product_id' in row else '',
                'product_name': row['product_name'] if 'product_name' in row else '',
                'pillar_team': row['pillar_team'] if 'pillar_team' in row else '',
                'prod_ytd_cost': row['prod_ytd_cost'] if 'prod_ytd_cost' in row else 0,
                'nonprod_ytd_cost': row['nonprod_ytd_cost'] if 'nonprod_ytd_cost' in row else 0,
                'total_ytd_cost': row['total_ytd_cost'] if 'total_ytd_cost' in row else 0,
                'nonprod_percentage': row['nonprod_percentage'] if 'nonprod_percentage' in row else 0
            })
        
        # Create static chart
        daily_trend_chart = create_daily_trend_chart(daily_trend_data)
        
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
            
            # Add BigQuery integration data
            'use_bigquery': use_bigquery,
            'project_id': project_id,
            'dataset': dataset,
            'cost_table': cost_table,
            'avg_table': avg_table,
            
            # Interactive charts flag
            'use_interactive_charts': use_interactive_charts,
            
            # Scorecard data
            'prod_ytd_cost': prod_ytd['ytd_cost'].iloc[0] if not prod_ytd.empty and 'ytd_cost' in prod_ytd.columns else 0,
            'nonprod_ytd_cost': nonprod_ytd['ytd_cost'].iloc[0] if not nonprod_ytd.empty and 'ytd_cost' in nonprod_ytd.columns else 0,
            'total_fy26_cost': total_fy26_cost,
            'prod_ytd_percent': prod_ytd_percent,
            'nonprod_ytd_percent': nonprod_ytd_percent,
            'fy26_percent': fy26_percent,
            'nonprod_percentage': nonprod_percentage,
            'nonprod_percentage_change': nonprod_percentage_change,
            
            # Recent comparisons
            'day_prod_cost': day_comparison[day_comparison['environment_type'] == 'PROD']['day4_cost'].iloc[0] if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values and 'day4_cost' in day_comparison.columns else 0,
            'day_nonprod_cost': day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day4_cost'].iloc[0] if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values and 'day4_cost' in day_comparison.columns else 0,
            'day_prod_percent': day_comparison[day_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values and 'percent_change' in day_comparison.columns else 0,
            'day_nonprod_percent': day_comparison[day_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values and 'percent_change' in day_comparison.columns else 0,
            
            'week_prod_cost': week_comparison[week_comparison['environment_type'] == 'PROD']['this_week_cost'].iloc[0] if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values and 'this_week_cost' in week_comparison.columns else 0,
            'week_nonprod_cost': week_comparison[week_comparison['environment_type'] == 'NON-PROD']['this_week_cost'].iloc[0] if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values and 'this_week_cost' in week_comparison.columns else 0,
            'week_prod_percent': week_comparison[week_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values and 'percent_change' in week_comparison.columns else 0,
            'week_nonprod_percent': week_comparison[week_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values and 'percent_change' in week_comparison.columns else 0,
            
            'month_prod_cost': month_comparison[month_comparison['environment_type'] == 'PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values and 'this_month_cost' in month_comparison.columns else 0,
            'month_nonprod_cost': month_comparison[month_comparison['environment_type'] == 'NON-PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and 'this_month_cost' in month_comparison.columns else 0,
            'month_prod_percent': month_comparison[month_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values and 'percent_change' in month_comparison.columns else 0,
            'month_nonprod_percent': month_comparison[month_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and 'percent_change' in month_comparison.columns else 0,
            
            # Static charts 
            'daily_trend_chart': daily_trend_chart,
            
            # Tables
            'product_cost_table': product_cost_table
        }
        
        # Add interactive charts data if enabled and plotly is available
        if use_interactive_charts and has_interactive_charts:
            # Create interactive charts
            daily_trend_chart_json = create_interactive_daily_trend_chart(daily_trend_data)
            product_chart_json = create_interactive_product_breakdown_chart(product_costs)
            env_chart_json = create_interactive_environment_breakdown_chart(ytd_costs)
            
            # Add to template data
            template_data['daily_trend_chart_json'] = daily_trend_chart_json
            template_data['product_chart_json'] = product_chart_json
            template_data['env_chart_json'] = env_chart_json
        else:
            # Disable interactive charts if plotly is not available
            template_data['use_interactive_charts'] = False
        
        # Render template and save to file
        html_output = template.render(**template_data)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
            
        logger.info(f"HTML report generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")
        raise