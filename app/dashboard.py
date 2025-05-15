"""
Dashboard generation for FinOps360 cost analysis.
"""
import os
import logging
import jinja2
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List, Tuple

from google.cloud import bigquery

from app.utils.config import FinOpsConfig, load_config
from app.utils.chart_config import are_charts_enabled

# Import interactive chart functionality
from app.utils.interactive_charts import (
    create_enhanced_daily_trend_chart,
    create_enhanced_cto_costs_chart, 
    create_enhanced_pillar_costs_chart,
    create_enhanced_product_costs_chart,
    generate_all_enhanced_charts
)

# Configure interactive charts (can be toggled in chart_config.py)
has_interactive_charts = are_charts_enabled()
from app.data_access import (
    get_ytd_costs,
    get_fy26_ytd_costs,
    get_fy26_costs,
    get_fy25_costs,
    get_recent_comparisons,
    get_product_costs,
    get_cto_costs,
    get_pillar_costs,
    get_daily_trend_data
)

# Import sample data for when BigQuery is not available
from app.utils.sample_data import (
    create_sample_ytd_costs,
    create_sample_fy26_ytd_costs,
    create_sample_fy26_costs,
    create_sample_fy25_costs,
    create_sample_day_comparison,
    create_sample_week_comparison,
    create_sample_month_comparison,
    create_sample_product_costs,
    create_sample_cto_costs,
    create_sample_pillar_costs,
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
        use_interactive_charts: Whether to generate interactive charts
        
    Returns:
        Path to the generated HTML report
    """
    try:
        # Load config settings for data display
        config = load_config("config.yaml")
        data_config = config.get('data', {})
        
        # Get configured comparison settings
        # Fixed dates for comparisons instead of offsets
        day_current_date = data_config.get('day_current_date', '2025-05-03')
        day_previous_date = data_config.get('day_previous_date', '2025-05-02')
        
        # Fixed week periods (start and end dates)
        week_current_start = data_config.get('week_current_start', '2025-04-27')
        week_current_end = data_config.get('week_current_end', '2025-05-03')
        week_previous_start = data_config.get('week_previous_start', '2025-04-20')
        week_previous_end = data_config.get('week_previous_end', '2025-04-26')
        
        # Fixed month periods
        month_current = data_config.get('month_current', '2025-04')
        month_previous = data_config.get('month_previous', '2025-03')
        
        top_products = data_config.get('top_products_count', 10)
        nonprod_threshold = data_config.get('nonprod_percentage_threshold', 30)
        display_millions = data_config.get('display_millions', True)
        
        try:
            # Get data from BigQuery
            ytd_costs = get_ytd_costs(client, project_id, dataset, cost_table)
            fy26_ytd_costs = get_fy26_ytd_costs(client, project_id, dataset, cost_table)
            fy26_costs = get_fy26_costs(client, project_id, dataset, cost_table)
            fy25_costs = get_fy25_costs(client, project_id, dataset, cost_table)
            day_comparison, week_comparison, month_comparison, date_info = get_recent_comparisons(
                client, project_id, dataset, cost_table, 
                day_current_date=day_current_date,
                day_previous_date=day_previous_date,
                week_current_start=week_current_start,
                week_current_end=week_current_end,
                week_previous_start=week_previous_start,
                week_previous_end=week_previous_end,
                month_current=month_current,
                month_previous=month_previous
            )
            product_costs = get_product_costs(
                client, project_id, dataset, cost_table,
                top_n=top_products,
                nonprod_pct_threshold=nonprod_threshold
            )
            cto_costs = get_cto_costs(
                client, project_id, dataset, cost_table,
                top_n=top_products
            )
            pillar_costs = get_pillar_costs(
                client, project_id, dataset, cost_table,
                top_n=top_products
            )
            daily_trend_data = get_daily_trend_data(client, project_id, dataset, avg_table)
            logger.info("Successfully retrieved data from BigQuery")
        except Exception as e:
            logger.error(f"Error retrieving data from BigQuery: {e}")
            
            # If tables don't exist, create sample data
            logger.info("Using sample data for dashboard generation")
            ytd_costs = create_sample_ytd_costs()
            fy26_ytd_costs = create_sample_fy26_ytd_costs()
            fy26_costs = create_sample_fy26_costs()
            fy25_costs = create_sample_fy25_costs()
            day_comparison = create_sample_day_comparison()
            week_comparison = create_sample_week_comparison()
            month_comparison = create_sample_month_comparison()
            # Use simple product data
            product_costs = create_sample_product_costs()
            cto_costs = create_sample_cto_costs()
            pillar_costs = create_sample_pillar_costs()
            print(f"Sample product costs created with {len(product_costs)} rows")
            if product_costs.empty:
                # Create a simple fallback data frame with minimal product data
                product_costs = pd.DataFrame({
                    'display_id': ['Platform - PROD-1000', 'Customer - PROD-1001'],
                    'product_name': ['Product 1', 'Product 2'],
                    'pillar_team': ['Platform', 'Customer'],
                    'prod_ytd_cost': [100000.0, 92000.0],
                    'nonprod_ytd_cost': [40000.0, 37000.0],
                    'total_ytd_cost': [140000.0, 129000.0]
                })
                print(f"Created fallback product costs with {len(product_costs)} rows")
            
            daily_trend_data = create_sample_daily_trend_data()
            date_info = create_sample_date_info()
        
        # Extract and process data (same regardless of source)
        prod_ytd = ytd_costs[ytd_costs['environment_type'] == 'PROD'] if not ytd_costs.empty and 'PROD' in ytd_costs['environment_type'].values else pd.DataFrame()
        nonprod_ytd = ytd_costs[ytd_costs['environment_type'] == 'NON-PROD'] if not ytd_costs.empty and 'NON-PROD' in ytd_costs['environment_type'].values else pd.DataFrame()

        # Extract FY26 YTD cost data
        prod_fy26_ytd = fy26_ytd_costs[fy26_ytd_costs['environment_type'] == 'PROD'] if not fy26_ytd_costs.empty and 'PROD' in fy26_ytd_costs['environment_type'].values else pd.DataFrame()
        nonprod_fy26_ytd = fy26_ytd_costs[fy26_ytd_costs['environment_type'] == 'NON-PROD'] if not fy26_ytd_costs.empty and 'NON-PROD' in fy26_ytd_costs['environment_type'].values else pd.DataFrame()

        prod_fy26 = fy26_costs[fy26_costs['environment_type'] == 'PROD'] if not fy26_costs.empty and 'PROD' in fy26_costs['environment_type'].values else pd.DataFrame()
        nonprod_fy26 = fy26_costs[fy26_costs['environment_type'] == 'NON-PROD'] if not fy26_costs.empty and 'NON-PROD' in fy26_costs['environment_type'].values else pd.DataFrame()

        prod_fy25 = fy25_costs[fy25_costs['environment_type'] == 'PROD'] if not fy25_costs.empty and 'PROD' in fy25_costs['environment_type'].values else pd.DataFrame()
        nonprod_fy25 = fy25_costs[fy25_costs['environment_type'] == 'NON-PROD'] if not fy25_costs.empty and 'NON-PROD' in fy25_costs['environment_type'].values else pd.DataFrame()
        
        # Get the YTD cost values first
        prod_ytd_cost = prod_ytd['ytd_cost'].iloc[0] if not prod_ytd.empty and 'ytd_cost' in prod_ytd.columns else 0
        nonprod_ytd_cost = nonprod_ytd['ytd_cost'].iloc[0] if not nonprod_ytd.empty and 'ytd_cost' in nonprod_ytd.columns else 0

        # Get the FY26 YTD cost values
        prod_fy26_ytd_cost = prod_fy26_ytd['ytd_cost'].iloc[0] if not prod_fy26_ytd.empty and 'ytd_cost' in prod_fy26_ytd.columns else 0
        nonprod_fy26_ytd_cost = nonprod_fy26_ytd['ytd_cost'].iloc[0] if not nonprod_fy26_ytd.empty and 'ytd_cost' in nonprod_fy26_ytd.columns else 0

        # Calculate total FY26 YTD cost
        total_fy26_ytd_cost = prod_fy26_ytd_cost + nonprod_fy26_ytd_cost

        # Get FY25 costs for comparison - now directly from the ytd_cost column
        prod_fy25_cost = 0
        nonprod_fy25_cost = 0

        # Get FY25 YTD costs for direct comparison with current YTD
        if not fy25_costs.empty and not prod_fy25.empty and 'ytd_cost' in prod_fy25.columns:
            prod_fy25_cost = prod_fy25['ytd_cost'].iloc[0]
            if prod_fy25_cost > 0:
                prod_ytd_percent = ((prod_ytd_cost - prod_fy25_cost) / prod_fy25_cost) * 100
            else:
                prod_ytd_percent = 0
        else:
            prod_ytd_percent = 0
            
        if not fy25_costs.empty and not nonprod_fy25.empty and 'ytd_cost' in nonprod_fy25.columns:
            nonprod_fy25_cost = nonprod_fy25['ytd_cost'].iloc[0]
            if nonprod_fy25_cost > 0:
                nonprod_ytd_percent = ((nonprod_ytd_cost - nonprod_fy25_cost) / nonprod_fy25_cost) * 100
            else:
                nonprod_ytd_percent = 0
        else:
            nonprod_ytd_percent = 0
        
        # Calculate total FY26 cost with percentage change vs FY25 YTD (not total FY25)
        total_fy26_cost = fy26_costs['total_cost'].sum() if not fy26_costs.empty and 'total_cost' in fy26_costs.columns else 0

        # Use FY25 YTD for percentage comparison, not total FY25
        total_fy25_ytd_cost = 0
        if not fy25_costs.empty and 'ytd_cost' in fy25_costs.columns:
            total_fy25_ytd_cost = fy25_costs['ytd_cost'].sum()
        else:
            total_fy25_ytd_cost = prod_fy25_cost + nonprod_fy25_cost

        # Store total FY25 cost for display - also use YTD cost, not total cost
        total_fy25_cost = total_fy25_ytd_cost

        # Calculate percentage change vs FY25 YTD
        fy26_ytd_percent = 0
        if total_fy25_ytd_cost > 0:
            fy26_ytd_percent = ((total_fy26_ytd_cost - total_fy25_ytd_cost) / total_fy25_ytd_cost) * 100

        # Calculate percentage change for Total FY26 Projected Cost vs FY25 YTD
        fy26_percent = 0
        if total_fy25_ytd_cost > 0:
            fy26_percent = ((total_fy26_cost - total_fy25_ytd_cost) / total_fy25_ytd_cost) * 100
        
        # Calculate overall nonprod percentage
        total_ytd_cost = 0
        if not ytd_costs.empty and 'ytd_cost' in ytd_costs.columns:
            total_ytd_cost = ytd_costs['ytd_cost'].sum()
            
        nonprod_ytd_cost = 0
        if not nonprod_ytd.empty and 'ytd_cost' in nonprod_ytd.columns:
            nonprod_ytd_cost = nonprod_ytd['ytd_cost'].iloc[0]
            
        # Calculate nonprod percentage
        if total_ytd_cost > 0:
            nonprod_percentage = (nonprod_ytd_cost / total_ytd_cost) * 100
        else:
            nonprod_percentage = 0
            
        # Calculate nonprod percentage change compared to FY25 - using YTD costs for both
        # We already have total_fy25_ytd_cost calculated above
        nonprod_fy25_ytd_cost = nonprod_fy25['ytd_cost'].iloc[0] if not nonprod_fy25.empty and 'ytd_cost' in nonprod_fy25.columns else 0
        
        if total_fy25_ytd_cost > 0:
            fy25_nonprod_percentage = (nonprod_fy25_ytd_cost / total_fy25_ytd_cost) * 100
            nonprod_percentage_change = nonprod_percentage - fy25_nonprod_percentage
        else:
            nonprod_percentage_change = 0
        
        # Process product cost table data
        if not product_costs.empty:
            product_cost_table = []
            for _, row in product_costs.iterrows():
                # Calculate nonprod percentage
                prod_cost = row.get('prod_ytd_cost', 0.0)
                nonprod_cost = row.get('nonprod_ytd_cost', 0.0)
                total_cost = row.get('total_ytd_cost', 0.0)
                if total_cost == 0 and (prod_cost > 0 or nonprod_cost > 0):
                    total_cost = prod_cost + nonprod_cost
                
                nonprod_percentage = (nonprod_cost / total_cost * 100) if total_cost > 0 else 0
                
                product_cost_table.append({
                    'product_id': row.get('display_id', ''),
                    'product_name': row.get('product_name', ''),
                    'pillar_team': row.get('pillar_team', ''),
                    'prod_ytd_cost': prod_cost,
                    'nonprod_ytd_cost': nonprod_cost,
                    'total_ytd_cost': total_cost,
                    'nonprod_percentage': nonprod_percentage
                })
        else:
            # Empty fallback instead of hardcoded data
            product_cost_table = []
            
        # Process CTO cost table data
        if not cto_costs.empty:
            cto_cost_table = []
            for _, row in cto_costs.iterrows():
                cto_cost_table.append({
                    'cto_org': row.get('cto_org', ''),
                    'prod_ytd_cost': row.get('prod_ytd_cost', 0.0),
                    'nonprod_ytd_cost': row.get('nonprod_ytd_cost', 0.0),
                    'total_ytd_cost': row.get('total_ytd_cost', 0.0),
                    'nonprod_percentage': row.get('nonprod_percentage', 0.0)
                })
        else:
            # Empty fallback instead of hardcoded data
            cto_cost_table = []
            
        # Process pillar cost table data
        if not pillar_costs.empty:
            pillar_cost_table = []
            for _, row in pillar_costs.iterrows():
                # Calculate nonprod percentage
                prod_cost = row.get('prod_ytd_cost', 0.0)
                nonprod_cost = row.get('nonprod_ytd_cost', 0.0)
                total_cost = row.get('total_ytd_cost', 0.0)
                if total_cost == 0 and (prod_cost > 0 or nonprod_cost > 0):
                    total_cost = prod_cost + nonprod_cost
                
                nonprod_percentage = (nonprod_cost / total_cost * 100) if total_cost > 0 else 0
                
                pillar_cost_table.append({
                    'pillar_name': row.get('pillar_name', ''),
                    'product_count': row.get('product_count', 0),
                    'prod_ytd_cost': prod_cost,
                    'nonprod_ytd_cost': nonprod_cost,
                    'total_ytd_cost': total_cost,
                    'nonprod_percentage': nonprod_percentage
                })
        else:
            # Empty fallback instead of hardcoded data
            pillar_cost_table = []
        
        print(f"Product cost table with {len(product_cost_table)} items")
        try:
            print(f"CTO cost table with {len(cto_cost_table)} items")
            print(f"Pillar cost table with {len(pillar_cost_table)} items")
        except NameError:
            # If the tables don't exist, create empty ones
            cto_cost_table = []
            pillar_cost_table = []
        
        # Generate charts if enabled
        daily_trend_chart = {"html": "", "json_data": "{}"}
        cto_costs_chart = {"html": "", "json_data": "{}"}
        pillar_costs_chart = {"html": "", "json_data": "{}"}
        product_costs_chart = {"html": "", "json_data": "{}"}
        
        if use_interactive_charts and has_interactive_charts:
            # Format daily trend data for charting
            if not daily_trend_data.empty:
                daily_trend_chart = create_enhanced_daily_trend_chart(daily_trend_data)
            
            # Format and create CTO costs chart
            if cto_cost_table:
                # Convert all values to numeric to avoid type errors
                cto_df = pd.DataFrame(cto_cost_table)
                numeric_columns = ['prod_ytd_cost', 'nonprod_ytd_cost', 'total_ytd_cost', 'nonprod_percentage']
                for col in numeric_columns:
                    if col in cto_df.columns:
                        cto_df[col] = pd.to_numeric(cto_df[col], errors='coerce').fillna(0)
                cto_costs_chart = create_enhanced_cto_costs_chart(cto_df)
            
            # Format and create pillar costs chart
            if pillar_cost_table:
                # Convert all values to numeric to avoid type errors
                pillar_df = pd.DataFrame(pillar_cost_table)
                numeric_columns = ['prod_ytd_cost', 'nonprod_ytd_cost', 'total_ytd_cost', 'product_count']
                for col in numeric_columns:
                    if col in pillar_df.columns:
                        pillar_df[col] = pd.to_numeric(pillar_df[col], errors='coerce').fillna(0)
                pillar_costs_chart = create_enhanced_pillar_costs_chart(pillar_df)
            else:
                # Create sample pillar data if none exists
                sample_pillar_data = create_sample_pillar_costs()
                pillar_costs_chart = create_enhanced_pillar_costs_chart(sample_pillar_data)
            
            # Format and create product costs chart
            if product_cost_table:
                # Convert all values to numeric to avoid type errors
                product_df = pd.DataFrame(product_cost_table)
                numeric_columns = ['prod_ytd_cost', 'nonprod_ytd_cost', 'total_ytd_cost', 'nonprod_percentage']
                for col in numeric_columns:
                    if col in product_df.columns:
                        product_df[col] = pd.to_numeric(product_df[col], errors='coerce').fillna(0)
                product_costs_chart = create_enhanced_product_costs_chart(product_df)
            else:
                # Create sample product data if none exists
                sample_product_data = create_sample_product_costs()
                product_costs_chart = create_enhanced_product_costs_chart(sample_product_data)
        
        # Load Jinja2 template
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        template = env.get_template(template_file)
        
        # Helper function to determine CSS class for percentage changes
        def get_percent_class(percent_change):
            if percent_change > 0:
                return "positive-change"  # Up/red (warning)
            elif percent_change < 0:
                return "negative-change"  # Down/green (good)
            else:
                return "neutral-change"   # No change

        # Prepare template data
        template_data = {
            'report_start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'report_end_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'report_generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

            # Add BigQuery integration data
            'project_id': project_id,
            'dataset': dataset,
            'cost_table': cost_table,
            'avg_table': avg_table,

            # Interactive charts flag
            'use_interactive_charts': use_interactive_charts,

            # Scorecard data
            'prod_ytd_cost': prod_ytd_cost,
            'nonprod_ytd_cost': nonprod_ytd_cost,
            'prod_fy26_ytd_cost': prod_fy26_ytd_cost,
            'nonprod_fy26_ytd_cost': nonprod_fy26_ytd_cost,
            'total_fy26_ytd_cost': total_fy26_ytd_cost,
            'total_fy25_ytd_cost': total_fy25_ytd_cost,
            'prod_fy25_cost': prod_fy25_cost,
            'nonprod_fy25_cost': nonprod_fy25_cost,
            'total_fy26_cost': total_fy26_cost,
            'total_fy25_cost': total_fy25_cost,
            'prod_ytd_percent': prod_ytd_percent,
            'nonprod_ytd_percent': nonprod_ytd_percent,
            'fy26_ytd_percent': fy26_ytd_percent,
            'fy26_percent': fy26_percent,
            'nonprod_percentage': nonprod_percentage,
            'nonprod_percentage_change': nonprod_percentage_change,

            # Add CSS classes for percentage changes
            'prod_ytd_percent_class': get_percent_class(prod_ytd_percent),
            'nonprod_ytd_percent_class': get_percent_class(nonprod_ytd_percent),
            'fy26_percent_class': get_percent_class(fy26_percent),
            'fy26_ytd_percent_class': get_percent_class(fy26_ytd_percent),
            'nonprod_percentage_change_class': get_percent_class(nonprod_percentage_change),

            # Recent comparisons
            'day_prod_cost': day_comparison[day_comparison['environment_type'] == 'PROD']['day_current_cost'].iloc[0] if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values and 'day_current_cost' in day_comparison.columns else 0,
            'day_nonprod_cost': day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_current_cost'].iloc[0] if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values and 'day_current_cost' in day_comparison.columns else 0,
            'day_prod_previous_cost': day_comparison[day_comparison['environment_type'] == 'PROD']['day_previous_cost'].iloc[0] if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values and 'day_previous_cost' in day_comparison.columns else 0,
            'day_nonprod_previous_cost': day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_previous_cost'].iloc[0] if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values and 'day_previous_cost' in day_comparison.columns else 0,
            'day_prod_percent': day_comparison[day_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values and 'percent_change' in day_comparison.columns else 0,
            'day_nonprod_percent': day_comparison[day_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values and 'percent_change' in day_comparison.columns else 0,

            'week_prod_cost': week_comparison[week_comparison['environment_type'] == 'PROD']['this_week_cost'].iloc[0] if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values and 'this_week_cost' in week_comparison.columns else 0,
            'week_nonprod_cost': week_comparison[week_comparison['environment_type'] == 'NON-PROD']['this_week_cost'].iloc[0] if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values and 'this_week_cost' in week_comparison.columns else 0,
            'week_prod_previous_cost': week_comparison[week_comparison['environment_type'] == 'PROD']['prev_week_cost'].iloc[0] if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values and 'prev_week_cost' in week_comparison.columns else 0,
            'week_nonprod_previous_cost': week_comparison[week_comparison['environment_type'] == 'NON-PROD']['prev_week_cost'].iloc[0] if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values and 'prev_week_cost' in week_comparison.columns else 0,
            'week_prod_percent': week_comparison[week_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values and 'percent_change' in week_comparison.columns else 0,
            'week_nonprod_percent': week_comparison[week_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values and 'percent_change' in week_comparison.columns else 0,

            'month_prod_cost': month_comparison[month_comparison['environment_type'] == 'PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values and 'this_month_cost' in month_comparison.columns else 0,
            'month_nonprod_cost': month_comparison[month_comparison['environment_type'] == 'NON-PROD']['this_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and 'this_month_cost' in month_comparison.columns else 0,
            'month_prod_previous_cost': month_comparison[month_comparison['environment_type'] == 'PROD']['prev_month_cost'].iloc[0] if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values and 'prev_month_cost' in month_comparison.columns else 0,
            'month_nonprod_previous_cost': month_comparison[month_comparison['environment_type'] == 'NON-PROD']['prev_month_cost'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and 'prev_month_cost' in month_comparison.columns else 0,
            'month_prod_percent': month_comparison[month_comparison['environment_type'] == 'PROD']['percent_change'].iloc[0] if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values and 'percent_change' in month_comparison.columns else 0,
            'month_nonprod_percent': month_comparison[month_comparison['environment_type'] == 'NON-PROD']['percent_change'].iloc[0] if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and 'percent_change' in month_comparison.columns else 0,

            # Calculate percentage changes if not in original data
            # For day comparison
            'day_prod_percent_calculated': ((day_comparison[day_comparison['environment_type'] == 'PROD']['day_current_cost'].iloc[0] /
                                          day_comparison[day_comparison['environment_type'] == 'PROD']['day_previous_cost'].iloc[0] - 1) * 100
                                         if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values and
                                         'day_current_cost' in day_comparison.columns and
                                         'day_previous_cost' in day_comparison.columns and
                                         day_comparison[day_comparison['environment_type'] == 'PROD']['day_previous_cost'].iloc[0] > 0
                                         else 0),
            'day_nonprod_percent_calculated': ((day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_current_cost'].iloc[0] /
                                              day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_previous_cost'].iloc[0] - 1) * 100
                                             if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values and
                                             'day_current_cost' in day_comparison.columns and
                                             'day_previous_cost' in day_comparison.columns and
                                             day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_previous_cost'].iloc[0] > 0
                                             else 0),

            # For week comparison
            'week_prod_percent_calculated': ((week_comparison[week_comparison['environment_type'] == 'PROD']['this_week_cost'].iloc[0] /
                                           week_comparison[week_comparison['environment_type'] == 'PROD']['prev_week_cost'].iloc[0] - 1) * 100
                                          if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values and
                                          'this_week_cost' in week_comparison.columns and
                                          'prev_week_cost' in week_comparison.columns and
                                          week_comparison[week_comparison['environment_type'] == 'PROD']['prev_week_cost'].iloc[0] > 0
                                          else 0),
            'week_nonprod_percent_calculated': ((week_comparison[week_comparison['environment_type'] == 'NON-PROD']['this_week_cost'].iloc[0] /
                                              week_comparison[week_comparison['environment_type'] == 'NON-PROD']['prev_week_cost'].iloc[0] - 1) * 100
                                             if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values and
                                             'this_week_cost' in week_comparison.columns and
                                             'prev_week_cost' in week_comparison.columns and
                                             week_comparison[week_comparison['environment_type'] == 'NON-PROD']['prev_week_cost'].iloc[0] > 0
                                             else 0),

            # For month comparison
            'month_prod_percent_calculated': ((month_comparison[month_comparison['environment_type'] == 'PROD']['this_month_cost'].iloc[0] /
                                            month_comparison[month_comparison['environment_type'] == 'PROD']['prev_month_cost'].iloc[0] - 1) * 100
                                           if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values and
                                           'this_month_cost' in month_comparison.columns and
                                           'prev_month_cost' in month_comparison.columns and
                                           month_comparison[month_comparison['environment_type'] == 'PROD']['prev_month_cost'].iloc[0] > 0
                                           else 0),
            'month_nonprod_percent_calculated': ((month_comparison[month_comparison['environment_type'] == 'NON-PROD']['this_month_cost'].iloc[0] /
                                               month_comparison[month_comparison['environment_type'] == 'NON-PROD']['prev_month_cost'].iloc[0] - 1) * 100
                                              if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and
                                              'this_month_cost' in month_comparison.columns and
                                              'prev_month_cost' in month_comparison.columns and
                                              month_comparison[month_comparison['environment_type'] == 'NON-PROD']['prev_month_cost'].iloc[0] > 0
                                              else 0),

            # Add CSS classes for percentage changes in comparisons
            'day_prod_percent_class': get_percent_class(
                ((day_comparison[day_comparison['environment_type'] == 'PROD']['day_current_cost'].iloc[0] /
                  day_comparison[day_comparison['environment_type'] == 'PROD']['day_previous_cost'].iloc[0] - 1) * 100
                 if not day_comparison.empty and 'PROD' in day_comparison['environment_type'].values and
                 'day_current_cost' in day_comparison.columns and
                 'day_previous_cost' in day_comparison.columns and
                 day_comparison[day_comparison['environment_type'] == 'PROD']['day_previous_cost'].iloc[0] > 0
                 else 0)
            ),
            'day_nonprod_percent_class': get_percent_class(
                ((day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_current_cost'].iloc[0] /
                  day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_previous_cost'].iloc[0] - 1) * 100
                 if not day_comparison.empty and 'NON-PROD' in day_comparison['environment_type'].values and
                 'day_current_cost' in day_comparison.columns and
                 'day_previous_cost' in day_comparison.columns and
                 day_comparison[day_comparison['environment_type'] == 'NON-PROD']['day_previous_cost'].iloc[0] > 0
                 else 0)
            ),
            'week_prod_percent_class': get_percent_class(
                ((week_comparison[week_comparison['environment_type'] == 'PROD']['this_week_cost'].iloc[0] /
                  week_comparison[week_comparison['environment_type'] == 'PROD']['prev_week_cost'].iloc[0] - 1) * 100
                 if not week_comparison.empty and 'PROD' in week_comparison['environment_type'].values and
                 'this_week_cost' in week_comparison.columns and
                 'prev_week_cost' in week_comparison.columns and
                 week_comparison[week_comparison['environment_type'] == 'PROD']['prev_week_cost'].iloc[0] > 0
                 else 0)
            ),
            'week_nonprod_percent_class': get_percent_class(
                ((week_comparison[week_comparison['environment_type'] == 'NON-PROD']['this_week_cost'].iloc[0] /
                  week_comparison[week_comparison['environment_type'] == 'NON-PROD']['prev_week_cost'].iloc[0] - 1) * 100
                 if not week_comparison.empty and 'NON-PROD' in week_comparison['environment_type'].values and
                 'this_week_cost' in week_comparison.columns and
                 'prev_week_cost' in week_comparison.columns and
                 week_comparison[week_comparison['environment_type'] == 'NON-PROD']['prev_week_cost'].iloc[0] > 0
                 else 0)
            ),
            'month_prod_percent_class': get_percent_class(
                ((month_comparison[month_comparison['environment_type'] == 'PROD']['this_month_cost'].iloc[0] /
                  month_comparison[month_comparison['environment_type'] == 'PROD']['prev_month_cost'].iloc[0] - 1) * 100
                 if not month_comparison.empty and 'PROD' in month_comparison['environment_type'].values and
                 'this_month_cost' in month_comparison.columns and
                 'prev_month_cost' in month_comparison.columns and
                 month_comparison[month_comparison['environment_type'] == 'PROD']['prev_month_cost'].iloc[0] > 0
                 else 0)
            ),
            'month_nonprod_percent_class': get_percent_class(
                ((month_comparison[month_comparison['environment_type'] == 'NON-PROD']['this_month_cost'].iloc[0] /
                  month_comparison[month_comparison['environment_type'] == 'NON-PROD']['prev_month_cost'].iloc[0] - 1) * 100
                 if not month_comparison.empty and 'NON-PROD' in month_comparison['environment_type'].values and
                 'this_month_cost' in month_comparison.columns and
                 'prev_month_cost' in month_comparison.columns and
                 month_comparison[month_comparison['environment_type'] == 'NON-PROD']['prev_month_cost'].iloc[0] > 0
                 else 0)
            ),

            # Date information for comparison section
            'day_current_date': date_info.get('day_current_date', ''),
            'day_previous_date': date_info.get('day_previous_date', ''),
            'week_current_date_range': date_info.get('week_current_date_range', ''),
            'week_previous_date_range': date_info.get('week_previous_date_range', ''),
            'month_current_date_range': date_info.get('month_current_date_range', ''),
            'month_previous_date_range': date_info.get('month_previous_date_range', ''),

            # Display in millions flag
            'display_in_millions': display_millions,

            # Static charts
            'daily_trend_chart': daily_trend_chart,

            # Tables
            'product_cost_table': product_cost_table,
            'cto_cost_table': cto_cost_table,
            'pillar_cost_table': pillar_cost_table
        }
        
        # Add the non-prod percentage threshold to template data
        template_data['nonprod_percentage_threshold'] = nonprod_threshold
        
        # Add interactive charts to template data
        template_data['use_interactive_charts'] = use_interactive_charts and has_interactive_charts
        template_data['daily_trend_chart'] = daily_trend_chart
        template_data['cto_costs_chart'] = cto_costs_chart
        template_data['pillar_costs_chart'] = pillar_costs_chart
        template_data['product_costs_chart'] = product_costs_chart
        
        # Debug template data
        print(f"Template data product_cost_table length: {len(template_data.get('product_cost_table', []))}")
        
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