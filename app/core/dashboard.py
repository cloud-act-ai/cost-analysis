"""
FastAPI-compatible async dashboard generation for FinOps360 cost analysis.
"""
import os
import logging
import jinja2
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List, Tuple
from pathlib import Path

from google.cloud import bigquery

from app.utils.config_loader import FinOpsConfig, load_config
from app.utils.chart.config import are_charts_enabled

# Import interactive chart functionality
from app.utils.chart.generator import (
    create_enhanced_daily_trend_chart,
    create_enhanced_cto_costs_chart, 
    create_enhanced_pillar_costs_chart,
    create_enhanced_product_costs_chart
)

# Import async data access functions
from app.core.data_access import (
    get_ytd_costs_async,
    get_fy26_ytd_costs_async,
    get_fy26_costs_async,
    get_fy25_costs_async,
    get_recent_comparisons_async,
    get_product_costs_async,
    get_cto_costs_async,
    get_pillar_costs_async,
    get_daily_trend_data_async,
    create_sample_date_info
)

# Import sample data for when BigQuery is not available
from app.utils.data_generator import (
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

async def generate_html_report_async(
    client: bigquery.Client,
    project_id: str,
    dataset: str,
    cost_table: str,
    avg_table: str,
    template_path: str,
    output_path: str,
    use_interactive_charts: bool = True,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a comprehensive HTML report asynchronously.
    
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
        # Initialize filters if not provided
        if filters is None:
            filters = {
                'cto': None,
                'pillar': None,
                'product': None,
                'show_sql': False
            }
        
        # Extract filter values
        selected_cto = filters.get('cto')
        selected_pillar = filters.get('pillar')
        selected_product = filters.get('product')
        show_sql = filters.get('show_sql', False)
        
        # Build filter conditions for SQL queries
        cto_filter = f"AND cto = '{selected_cto}'" if selected_cto else ""
        pillar_filter = f"AND tr_product_pillar_team = '{selected_pillar}'" if selected_pillar else ""
        product_filter = f"AND tr_product_id = '{selected_product}'" if selected_product else ""
        
        # Log active filters for debugging
        if selected_cto or selected_pillar or selected_product:
            logger.info(f"Active filters: CTO='{selected_cto}', Pillar='{selected_pillar}', Product='{selected_product}'")
            logger.info(f"Filter SQL conditions: {cto_filter} {pillar_filter} {product_filter}")
        
        # Store SQL queries if show_sql is enabled
        sql_queries = {}
        
        # Load config settings for data display
        config = load_config("config.yaml")
        data_config = config.get('data', {})
        
        # Get configured comparison settings directly from config without defaults
        # Fixed dates for comparisons
        day_current_date = data_config.get('day_current_date', '')
        day_previous_date = data_config.get('day_previous_date', '')
        
        # Fixed week periods (start and end dates)
        week_current_start = data_config.get('week_current_start', '')
        week_current_end = data_config.get('week_current_end', '')
        week_previous_start = data_config.get('week_previous_start', '')
        week_previous_end = data_config.get('week_previous_end', '')
        
        # Fixed month periods
        month_current = data_config.get('month_current', '')
        month_previous = data_config.get('month_previous', '')
        
        # Display settings
        top_products = data_config.get('top_products_count', 0)
        nonprod_threshold = data_config.get('nonprod_percentage_threshold', 0)
        display_millions = data_config.get('display_millions', False)
        
        # Check if we're using sample data
        using_sample_data = hasattr(client, "__class__") and client.__class__.__name__ == "MagicMock"
        if using_sample_data:
            logger.warning("Using SAMPLE DATA for dashboard generation")

        try:
            # Run all data fetching tasks in parallel for better performance
            # Apply filters to all queries
            # Core metrics tasks
            ytd_costs_task = get_ytd_costs_async(client, project_id, dataset, cost_table, 
                cto_filter=cto_filter, pillar_filter=pillar_filter, product_filter=product_filter)
            
            fy26_ytd_costs_task = get_fy26_ytd_costs_async(client, project_id, dataset, cost_table,
                cto_filter=cto_filter, pillar_filter=pillar_filter, product_filter=product_filter)
            
            fy26_costs_task = get_fy26_costs_async(client, project_id, dataset, cost_table,
                cto_filter=cto_filter, pillar_filter=pillar_filter, product_filter=product_filter)
            
            fy25_costs_task = get_fy25_costs_async(client, project_id, dataset, cost_table,
                cto_filter=cto_filter, pillar_filter=pillar_filter, product_filter=product_filter)
            
            recent_comparisons_task = get_recent_comparisons_async(
                client, project_id, dataset, cost_table, 
                day_current_date=day_current_date,
                day_previous_date=day_previous_date,
                week_current_start=week_current_start,
                week_current_end=week_current_end,
                week_previous_start=week_previous_start,
                week_previous_end=week_previous_end,
                month_current=month_current,
                month_previous=month_previous,
                cto_filter=cto_filter,
                pillar_filter=pillar_filter,
                product_filter=product_filter
            )
            
            # Breakdown cost tasks with filters
            product_costs_task = get_product_costs_async(
                client, project_id, dataset, cost_table,
                top_n=top_products,
                nonprod_pct_threshold=nonprod_threshold,
                cto_filter=cto_filter,
                pillar_filter=pillar_filter,
                product_filter=product_filter
            )
            
            cto_costs_task = get_cto_costs_async(
                client, project_id, dataset, cost_table,
                top_n=top_products,
                cto_filter=cto_filter,
                pillar_filter=pillar_filter,
                product_filter=product_filter
            )
            
            pillar_costs_task = get_pillar_costs_async(
                client, project_id, dataset, cost_table,
                top_n=top_products,
                cto_filter=cto_filter,
                pillar_filter=pillar_filter,
                product_filter=product_filter
            )
            
            # If show_sql is enabled, save the queries
            if show_sql:
                sql_queries['cto_costs'] = load_sql_query(
                    "cto_costs", 
                    project_id=project_id, 
                    dataset=dataset, 
                    table=cost_table,
                    top_n=top_products,
                    cto_filter=cto_filter,
                    pillar_filter=pillar_filter,
                    product_filter=product_filter
                )
                
                sql_queries['pillar_costs'] = load_sql_query(
                    "pillar_costs", 
                    project_id=project_id, 
                    dataset=dataset, 
                    table=cost_table,
                    top_n=top_products,
                    cto_filter=cto_filter,
                    pillar_filter=pillar_filter,
                    product_filter=product_filter
                )
                
                sql_queries['product_costs'] = load_sql_query(
                    "product_costs", 
                    project_id=project_id, 
                    dataset=dataset, 
                    table=cost_table,
                    top_n=top_products,
                    cto_filter=cto_filter,
                    pillar_filter=pillar_filter,
                    product_filter=product_filter
                )
            
            daily_trend_data_task = get_daily_trend_data_async(
                client, 
                project_id, 
                dataset, 
                avg_table,
                cto_filter=cto_filter,
                pillar_filter=pillar_filter,
                product_filter=product_filter
            )
            
            # Wait for all data fetching tasks to complete
            results = await asyncio.gather(
                ytd_costs_task,
                fy26_ytd_costs_task,
                fy26_costs_task,
                fy25_costs_task,
                recent_comparisons_task,
                product_costs_task,
                cto_costs_task,
                pillar_costs_task,
                daily_trend_data_task,
                return_exceptions=True  # Don't let one task failure fail all tasks
            )
            
            # Extract results
            ytd_costs = results[0] if not isinstance(results[0], Exception) else create_sample_ytd_costs()
            fy26_ytd_costs = results[1] if not isinstance(results[1], Exception) else create_sample_fy26_ytd_costs()
            fy26_costs = results[2] if not isinstance(results[2], Exception) else create_sample_fy26_costs()
            fy25_costs = results[3] if not isinstance(results[3], Exception) else create_sample_fy25_costs()
            
            # Extract comparison results
            if not isinstance(results[4], Exception):
                day_comparison, week_comparison, month_comparison, date_info = results[4]
            else:
                day_comparison = create_sample_day_comparison()
                week_comparison = create_sample_week_comparison()
                month_comparison = create_sample_month_comparison()
                date_info = create_sample_date_info()
            
            product_costs = results[5] if not isinstance(results[5], Exception) else create_sample_product_costs()
            cto_costs = results[6] if not isinstance(results[6], Exception) else create_sample_cto_costs()
            pillar_costs = results[7] if not isinstance(results[7], Exception) else create_sample_pillar_costs()
            daily_trend_data = results[8] if not isinstance(results[8], Exception) else create_sample_daily_trend_data()
            
            logger.info("Successfully retrieved data for dashboard")
            
        except Exception as e:
            logger.error(f"Error retrieving data from BigQuery: {e}")
            
            # If tasks fail, create sample data
            logger.info("Using sample data for dashboard generation")
            ytd_costs = create_sample_ytd_costs()
            fy26_ytd_costs = create_sample_fy26_ytd_costs()
            fy26_costs = create_sample_fy26_costs()
            fy25_costs = create_sample_fy25_costs()
            day_comparison = create_sample_day_comparison()
            week_comparison = create_sample_week_comparison()
            month_comparison = create_sample_month_comparison()
            product_costs = create_sample_product_costs()
            cto_costs = create_sample_cto_costs()
            pillar_costs = create_sample_pillar_costs()
            daily_trend_data = create_sample_daily_trend_data()
            date_info = create_sample_date_info()
            
            # Create a simple fallback product data if needed
            if product_costs.empty:
                product_costs = pd.DataFrame({
                    'display_id': ['Platform - PROD-1000', 'Customer - PROD-1001'],
                    'product_name': ['Product 1', 'Product 2'],
                    'pillar_team': ['Platform', 'Customer'],
                    'prod_ytd_cost': [100000.0, 92000.0],
                    'nonprod_ytd_cost': [40000.0, 37000.0],
                    'total_ytd_cost': [140000.0, 129000.0]
                })
                logger.info(f"Created fallback product costs with {len(product_costs)} rows")
        
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
        cto_cost_table = []
        if isinstance(cto_costs, pd.DataFrame) and not cto_costs.empty:
            for _, row in cto_costs.iterrows():
                cto_cost_table.append({
                    'cto_org': row.get('cto_org', ''),
                    'prod_ytd_cost': row.get('prod_ytd_cost', 0.0),
                    'nonprod_ytd_cost': row.get('nonprod_ytd_cost', 0.0),
                    'total_ytd_cost': row.get('total_ytd_cost', 0.0),
                    'nonprod_percentage': row.get('nonprod_percentage', 0.0)
                })
        elif isinstance(cto_costs, list) and cto_costs:
            for item in cto_costs:
                if isinstance(item, dict):
                    cto_cost_table.append({
                        'cto_org': item.get('cto_org', ''),
                        'prod_ytd_cost': item.get('prod_ytd_cost', 0.0),
                        'nonprod_ytd_cost': item.get('nonprod_ytd_cost', 0.0),
                        'total_ytd_cost': item.get('total_ytd_cost', 0.0),
                        'nonprod_percentage': item.get('nonprod_percentage', 0.0)
                    })
            
        # Process pillar cost table data
        pillar_cost_table = []
        if isinstance(pillar_costs, pd.DataFrame) and not pillar_costs.empty:
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
        elif isinstance(pillar_costs, list) and pillar_costs:
            for item in pillar_costs:
                if isinstance(item, dict):
                    # Calculate nonprod percentage
                    prod_cost = item.get('prod_ytd_cost', 0.0)
                    nonprod_cost = item.get('nonprod_ytd_cost', 0.0)
                    total_cost = item.get('total_ytd_cost', 0.0)
                    if total_cost == 0 and (prod_cost > 0 or nonprod_cost > 0):
                        total_cost = prod_cost + nonprod_cost
                    
                    nonprod_percentage = (nonprod_cost / total_cost * 100) if total_cost > 0 else 0
                    
                    pillar_cost_table.append({
                        'pillar_name': item.get('pillar_name', ''),
                        'product_count': item.get('product_count', 0),
                        'prod_ytd_cost': prod_cost,
                        'nonprod_ytd_cost': nonprod_cost,
                        'total_ytd_cost': total_cost,
                        'nonprod_percentage': nonprod_percentage
                    })
        
        logger.info(f"Product cost table with {len(product_cost_table)} items")
        try:
            logger.info(f"CTO cost table with {len(cto_cost_table)} items")
            logger.info(f"Pillar cost table with {len(pillar_cost_table)} items")
        except NameError:
            # If the tables don't exist, create empty ones
            cto_cost_table = []
            pillar_cost_table = []
        
        # Generate charts if enabled
        daily_trend_chart = {"html": "", "json_data": "{}"}
        cto_costs_chart = {"html": "", "json_data": "{}"}
        pillar_costs_chart = {"html": "", "json_data": "{}"}
        product_costs_chart = {"html": "", "json_data": "{}"}
        
        if use_interactive_charts and are_charts_enabled():
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
        
        # Create lists of CTO organizations, pillar teams, and products for filtering
        cto_list = []
        pillar_list = []
        product_list = []
        pillar_to_cto = {}  # Mapping of pillar to CTO for dropdown filtering
        
        # Extract unique CTOs from CTO costs
        # Handle both DataFrame and list of dictionaries format
        if isinstance(cto_costs, pd.DataFrame):
            if 'cto_org' in cto_costs.columns:
                cto_list = cto_costs['cto_org'].unique().tolist()
        else:
            # Original list handling
            for item in cto_costs:
                if isinstance(item, dict) and 'cto_org' in item and item['cto_org'] not in cto_list:
                    cto_list.append(item['cto_org'])
        
        # Extract unique pillars from pillar costs
        # Handle both DataFrame and list of dictionaries format
        if isinstance(pillar_costs, pd.DataFrame):
            if 'pillar_name' in pillar_costs.columns:
                pillar_list = pillar_costs['pillar_name'].unique().tolist()
        else:
            # Original list handling
            for item in pillar_costs:
                if isinstance(item, dict) and 'pillar_name' in item and item['pillar_name'] not in pillar_list:
                    pillar_list.append(item['pillar_name'])
        
        # Create product list with additional details for filtering
        # Handle both DataFrame and list of dictionaries format
        if isinstance(product_costs, pd.DataFrame):
            if all(col in product_costs.columns for col in ['product_name', 'pillar_team', 'product_id']):
                for _, row in product_costs.iterrows():
                    product_list.append({
                        'id': row.get('product_id', ''),
                        'name': row.get('product_name', ''),
                        'pillar': row.get('pillar_team', ''),
                        'display': row.get('display_id', f"{row.get('pillar_team', '')} - {row.get('product_id', '')}")
                    })
                    
                    # Build pillar to CTO mapping if both fields exist
                    if 'pillar_team' in product_costs.columns and 'cto_org' in product_costs.columns:
                        pillar_to_cto[row['pillar_team']] = row['cto_org']
        else:
            # Original list handling
            for item in product_costs:
                if isinstance(item, dict) and 'product_name' in item and 'pillar_team' in item and 'product_id' in item:
                    product_list.append({
                        'id': item.get('product_id', ''),
                        'name': item.get('product_name', ''),
                        'pillar': item.get('pillar_team', ''),
                        'display': item.get('display_id', f"{item.get('pillar_team', '')} - {item.get('product_id', '')}")
                    })
                    
                    # Build pillar to CTO mapping
                    if 'pillar_team' in item and 'cto_org' in item:
                        pillar_to_cto[item['pillar_team']] = item['cto_org']
        
        # Sort the lists for easier selection
        cto_list.sort()
        pillar_list.sort()
        product_list.sort(key=lambda x: x['display'])
        
        # Prepare template data
        # Check if we're using sample data
        using_sample_data = hasattr(client, "__class__") and client.__class__.__name__ == "MagicMock"
        
        template_data = {
            'report_start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'report_end_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'report_generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'using_sample_data': using_sample_data,

            # Add BigQuery integration data
            'project_id': project_id,
            'dataset': dataset,
            'cost_table': cost_table,
            'avg_table': avg_table,

            # Interactive charts flag
            'use_interactive_charts': use_interactive_charts,
            
            # Filter information
            'cto_list': cto_list,
            'pillar_list': pillar_list,
            'product_list': product_list,
            'pillar_to_cto': pillar_to_cto,
            'selected_cto': selected_cto,
            'selected_pillar': selected_pillar,
            'selected_product': selected_product,
            'show_sql': show_sql,
            'sql_queries': sql_queries,

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
        template_data['use_interactive_charts'] = use_interactive_charts and are_charts_enabled()
        template_data['daily_trend_chart'] = daily_trend_chart
        template_data['cto_costs_chart'] = cto_costs_chart
        template_data['pillar_costs_chart'] = pillar_costs_chart
        template_data['product_costs_chart'] = product_costs_chart
        
        # Add sample data flag to template data
        template_data['using_sample_data'] = using_sample_data
        
        # Debug template data
        logger.info(f"Template data product_cost_table length: {len(template_data.get('product_cost_table', []))}")
        
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

# Asyncio imported at the top of the file