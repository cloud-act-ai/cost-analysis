"""
Interactive chart utilities for FinOps360 cost analysis dashboard.
"""
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

def create_interactive_daily_trend_chart(df: pd.DataFrame) -> str:
    """
    Create an interactive daily trend chart with both actual and forecasted costs.
    
    Args:
        df: DataFrame with daily cost data
        
    Returns:
        JSON representation of the Plotly figure
    """
    try:
        # Check if dataframe is empty
        if df.empty:
            # Create a simple figure with a message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for trend chart",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="Daily Cost Analysis for PROD and NON-PROD Environments",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        # Create the figure
        fig = go.Figure()
        
        # Define colors - enhanced for better contrast and visual appeal
        prod_color = '#4285F4'  # Bright blue for PROD
        nonprod_color = '#34A853'  # Bright green for NON-PROD
        avg_color = '#666666'  # Gray for averages
        forecast_prod_color = '#9966ff'  # Purple for PROD forecast
        forecast_nonprod_color = '#ff6666'  # Red for NON-PROD forecast
        
        # Get unique environments
        environments = df['environment_type'].unique()
        
        # Process each environment type
        for env in environments:
            env_data = df[df['environment_type'] == env]
            
            # Line color based on environment
            color = prod_color if env == 'PROD' else nonprod_color
            forecast_color = forecast_prod_color if env == 'PROD' else forecast_nonprod_color
            
            # Add actual daily cost line
            fig.add_trace(go.Scatter(
                x=env_data['date'],
                y=env_data['daily_cost'],
                mode='lines',
                name=f"{env} Daily Cost (FY26)",
                line=dict(color=color, width=2.5, shape='spline', smoothing=0.3),
                hovertemplate='%{x|%b %d, %Y}: $%{y:,.2f}<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title="FY26 Daily Cost Trend",
            title_x=0.5,
            xaxis_title="Date",
            yaxis_title="Cost ($)",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=100, b=50),
            height=500,
            yaxis=dict(
                tickprefix="$",
                separatethousands=True,
                range=[0, None],  # Start y-axis from 0
                nticks=10,  # Specify approximate number of ticks
                tickmode='auto',
                showgrid=True,
                gridcolor='rgba(211,211,211,0.5)',
                gridwidth=1,
                mirror=True,
                showline=True,
                linecolor='rgba(211,211,211,1)',
                linewidth=1
            ),
            xaxis=dict(
                tickformat="%b %Y",
                tickangle=-45,
                showgrid=True,
                gridcolor='rgba(211,211,211,0.5)',
                gridwidth=1,
                mirror=True,
                showline=True,
                linecolor='rgba(211,211,211,1)',
                linewidth=1,
                nticks=12  # Show approximately one tick per month
            ),
            plot_bgcolor='rgba(245,247,249,0.8)',
            paper_bgcolor='rgba(245,247,249,0.8)',
            font=dict(
                family="Segoe UI, Arial, sans-serif"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Segoe UI, Arial, sans-serif"
            )
        )
        
        # We've moved grid line settings to the axis configuration
        
        # Make the figure responsive
        fig.update_layout(
            autosize=True,
            legend_title_text="",
            legend_title_font_size=10
        )
        
        # Add chart filter buttons in a more accessible layout
        button_layer_1_height = 1.12
        
        fig.update_layout(
            # Create a row of buttons for environment filtering
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.5,
                    y=button_layer_1_height,
                    xanchor="center",
                    yanchor="top",
                    buttons=[
                        dict(
                            label="👁️ Show All",
                            method="update",
                            args=[{"visible": [True] * len(fig.data)}]
                        ),
                        dict(
                            label="🔵 PROD Only",
                            method="update",
                            args=[{"visible": [True if "PROD" in trace.name and "NON-PROD" not in trace.name else False 
                                               for trace in fig.data]}]
                        ),
                        dict(
                            label="🟢 NON-PROD Only",
                            method="update",
                            args=[{"visible": [True if "NON-PROD" in trace.name else False 
                                               for trace in fig.data]}]
                        )
                    ]
                )
            ]
        )
        
        # Add extra margin at the top for the buttons
        fig.update_layout(margin=dict(t=120))
        
        # Convert to JSON
        plotly_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        return plotly_json
        
    except Exception as e:
        logger.error(f"Error creating interactive daily trend chart: {e}")
        # Return a minimal valid JSON if there's an error
        return json.dumps({"data": [], "layout": {"title": "Error creating chart"}})


def create_interactive_product_breakdown_chart(product_df: pd.DataFrame, top_n: int = 10) -> str:
    """
    Create an interactive chart showing top products by cost.
    
    Args:
        product_df: DataFrame with product cost data
        top_n: Number of top products to display
        
    Returns:
        JSON representation of the Plotly figure
    """
    try:
        # Check for empty dataframe or missing columns
        required_columns = ['product_name', 'total_ytd_cost', 'prod_ytd_cost', 'nonprod_ytd_cost']
        has_required_data = (not product_df.empty and 
                           all(col in product_df.columns for col in ['product_name']) and
                           ('total_ytd_cost' in product_df.columns or 'prod_ytd_cost' in product_df.columns))
        
        if not has_required_data:
            # Create empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text="No product cost data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="Top Products by Cost",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
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
                    'total_ytd_cost': total_cost,
                    'nonprod_percentage': (nonprod_cost / total_cost * 100) if total_cost > 0 else 0
                })
            
            if summary:
                # Convert to DataFrame and sort
                summary_df = pd.DataFrame(summary)
                top_products = summary_df.sort_values('total_ytd_cost', ascending=False)
        
        # Check if we have any products
        if top_products.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No product cost data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="Top Products by Cost",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        # Sort products by total cost
        sorted_products = top_products.sort_values('total_ytd_cost', ascending=True)
        
        # Create horizontal bar chart for PROD costs only
        fig = go.Figure()
        
        # Use display_id field if available, otherwise fall back to product_name
        display_field = 'display_id' if 'display_id' in sorted_products.columns else 'product_name'
        
        # Add production costs only
        fig.add_trace(go.Bar(
            y=sorted_products[display_field],
            x=sorted_products['prod_ytd_cost'],
            name='PROD',
            orientation='h',
            marker=dict(color='#3366cc'),
            hovertemplate='<b>%{y}</b><br>PROD: $%{x:,.2f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="Top Products by Cost (PROD Only)",
            title_x=0.5,
            xaxis_title="Cost ($)",
            barmode='group',
            height=max(400, 100 + (30 * len(sorted_products))),  # Adjust height based on number of products
            margin=dict(l=200, r=50, t=100, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                tickprefix="$",
                separatethousands=True
            ),
            plot_bgcolor='rgba(245,247,249,0.8)',
            paper_bgcolor='rgba(245,247,249,0.8)',
            font=dict(
                family="Segoe UI, Arial, sans-serif"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Segoe UI, Arial, sans-serif"
            )
        )
        
        # Add product cost annotation
        for i, row in enumerate(sorted_products.itertuples()):
            # Add text at the end of the bar
            fig.add_annotation(
                x=row.prod_ytd_cost,
                y=row.product_name,
                text=f" ${row.prod_ytd_cost:,.2f}",
                showarrow=False,
                xshift=10,
                font=dict(size=10),
                xanchor="left"
            )
        
        # Keep only the stacked view without toggle buttons
        # No interactivity buttons needed as requested
        
        # Convert to JSON
        return json.dumps(fig, cls=PlotlyJSONEncoder)
        
    except Exception as e:
        logger.error(f"Error creating interactive product breakdown chart: {e}")
        # Return a minimal valid JSON if there's an error
        return json.dumps({"data": [], "layout": {"title": "Error creating chart"}})


def create_interactive_cto_breakdown_chart(cto_df: pd.DataFrame, top_n: int = 10) -> str:
    """
    Create an interactive chart showing CTO organization costs.
    
    Args:
        cto_df: DataFrame with CTO organization cost data
        top_n: Number of top CTOs to display
        
    Returns:
        JSON representation of the Plotly figure
    """
    try:
        # Check for empty dataframe or missing columns
        required_columns = ['cto_org', 'total_ytd_cost', 'prod_ytd_cost', 'nonprod_ytd_cost']
        has_required_data = (not cto_df.empty and 
                           'cto_org' in cto_df.columns and
                           ('total_ytd_cost' in cto_df.columns or 'prod_ytd_cost' in cto_df.columns))
        
        if not has_required_data:
            # Create empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text="No CTO organization cost data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="CTO Organization Costs",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        # Ensure we have the necessary cost columns or create them
        if 'total_ytd_cost' not in cto_df.columns and 'prod_ytd_cost' in cto_df.columns and 'nonprod_ytd_cost' in cto_df.columns:
            cto_df['total_ytd_cost'] = cto_df['prod_ytd_cost'] + cto_df['nonprod_ytd_cost']
        
        # Get top N CTOs by total cost
        sort_column = 'total_ytd_cost' if 'total_ytd_cost' in cto_df.columns else 'prod_ytd_cost'
        top_ctos = cto_df.sort_values(sort_column, ascending=False).head(top_n)
            
        # Check if we have any CTO data
        if top_ctos.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No CTO organization cost data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="CTO Organization Costs",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        # Sort CTOs by total cost
        sorted_ctos = top_ctos.sort_values('total_ytd_cost', ascending=True)
        
        # Create horizontal bar chart for only PROD costs
        fig = go.Figure()
        
        # Add production costs only
        fig.add_trace(go.Bar(
            y=sorted_ctos['cto_org'],
            x=sorted_ctos['prod_ytd_cost'],
            name='PROD',
            orientation='h',
            marker=dict(color='#4285F4'),
            hovertemplate='<b>%{y}</b><br>PROD: $%{x:,.2f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="CTO Organization Costs (PROD Only)",
            title_x=0.5,
            xaxis_title="Cost ($)",
            barmode='group',
            height=max(400, 100 + (30 * len(sorted_ctos))),
            margin=dict(l=200, r=50, t=100, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                tickprefix="$",
                separatethousands=True
            ),
            plot_bgcolor='rgba(245,247,249,0.8)',
            paper_bgcolor='rgba(245,247,249,0.8)',
            font=dict(
                family="Segoe UI, Arial, sans-serif"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Segoe UI, Arial, sans-serif"
            )
        )
        
        # Add CTO cost annotation
        for i, row in enumerate(sorted_ctos.itertuples()):
            # Add text at the end of the bar
            fig.add_annotation(
                x=row.prod_ytd_cost,
                y=row.cto_org,
                text=f" ${row.prod_ytd_cost:,.2f}",
                showarrow=False,
                xshift=10,
                font=dict(size=10),
                xanchor="left"
            )
        
        # Convert to JSON
        return json.dumps(fig, cls=PlotlyJSONEncoder)
        
    except Exception as e:
        logger.error(f"Error creating interactive CTO breakdown chart: {e}")
        # Return a minimal valid JSON if there's an error
        return json.dumps({"data": [], "layout": {"title": "Error creating chart"}})


def create_interactive_pillar_breakdown_chart(pillar_df: pd.DataFrame, top_n: int = 10) -> str:
    """
    Create an interactive chart showing product pillar team costs.
    
    Args:
        pillar_df: DataFrame with pillar team cost data
        top_n: Number of top pillars to display
        
    Returns:
        JSON representation of the Plotly figure
    """
    try:
        # Check for empty dataframe or missing columns
        required_columns = ['pillar_name', 'total_ytd_cost', 'prod_ytd_cost', 'nonprod_ytd_cost']
        has_required_data = (not pillar_df.empty and 
                           'pillar_name' in pillar_df.columns and
                           ('total_ytd_cost' in pillar_df.columns or 'prod_ytd_cost' in pillar_df.columns))
        
        if not has_required_data:
            # Create empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text="No pillar team cost data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="Product Pillar Team Costs",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        # Ensure we have the necessary cost columns or create them
        if 'total_ytd_cost' not in pillar_df.columns and 'prod_ytd_cost' in pillar_df.columns and 'nonprod_ytd_cost' in pillar_df.columns:
            pillar_df['total_ytd_cost'] = pillar_df['prod_ytd_cost'] + pillar_df['nonprod_ytd_cost']
        
        # Get top N pillars by total cost
        sort_column = 'total_ytd_cost' if 'total_ytd_cost' in pillar_df.columns else 'prod_ytd_cost'
        top_pillars = pillar_df.sort_values(sort_column, ascending=False).head(top_n)
            
        # Check if we have any pillar data
        if top_pillars.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No pillar team cost data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="Product Pillar Team Costs",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        # Sort pillars by total cost
        sorted_pillars = top_pillars.sort_values('total_ytd_cost', ascending=True)
        
        # Create horizontal bar chart for PROD costs only
        fig = go.Figure()
        
        # Add production costs only
        fig.add_trace(go.Bar(
            y=sorted_pillars['pillar_name'],
            x=sorted_pillars['prod_ytd_cost'],
            name='PROD',
            orientation='h',
            marker=dict(color='#4285F4'),
            hovertemplate='<b>%{y}</b><br>PROD: $%{x:,.2f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="Product Pillar Team Costs (PROD Only)",
            title_x=0.5,
            xaxis_title="Cost ($)",
            barmode='group',
            height=max(400, 100 + (30 * len(sorted_pillars))),
            margin=dict(l=200, r=50, t=100, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                tickprefix="$",
                separatethousands=True
            ),
            plot_bgcolor='rgba(245,247,249,0.8)',
            paper_bgcolor='rgba(245,247,249,0.8)',
            font=dict(
                family="Segoe UI, Arial, sans-serif"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Segoe UI, Arial, sans-serif"
            )
        )
        
        # Add pillar cost annotation
        for i, row in enumerate(sorted_pillars.itertuples()):
            product_count = getattr(row, 'product_count', 0)
            if pd.isna(product_count):
                product_count = 0
                
            # Add text at the end of the bar
            fig.add_annotation(
                x=row.prod_ytd_cost,
                y=row.pillar_name,
                text=f" ${row.prod_ytd_cost:,.2f} ({product_count} products)",
                showarrow=False,
                xshift=10,
                font=dict(size=10),
                xanchor="left"
            )
        
        # Convert to JSON
        return json.dumps(fig, cls=PlotlyJSONEncoder)
        
    except Exception as e:
        logger.error(f"Error creating interactive pillar breakdown chart: {e}")
        # Return a minimal valid JSON if there's an error
        return json.dumps({"data": [], "layout": {"title": "Error creating chart"}})


def create_interactive_environment_breakdown_chart(ytd_costs: pd.DataFrame) -> str:
    """
    Create an interactive chart showing environment cost breakdown.
    
    Args:
        ytd_costs: DataFrame with YTD costs by environment
        
    Returns:
        JSON representation of the Plotly figure
    """
    try:
        # Check if we have data
        if ytd_costs.empty or 'environment_type' not in ytd_costs.columns or 'ytd_cost' not in ytd_costs.columns:
            # No data available, create empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text="No environment cost data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            fig.update_layout(
                title="Cost Breakdown by Environment",
                title_x=0.5
            )
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        # Extract production and non-production costs
        prod_costs = ytd_costs[ytd_costs['environment_type'] == 'PROD']['ytd_cost'].iloc[0] \
            if 'PROD' in ytd_costs['environment_type'].values else 0
            
        nonprod_costs = ytd_costs[ytd_costs['environment_type'] == 'NON-PROD']['ytd_cost'].iloc[0] \
            if 'NON-PROD' in ytd_costs['environment_type'].values else 0
        
        # Calculate total and percentages
        total_cost = prod_costs + nonprod_costs
        prod_pct = (prod_costs / total_cost * 100) if total_cost > 0 else 0
        nonprod_pct = (nonprod_costs / total_cost * 100) if total_cost > 0 else 0
        
        # Create the pie chart
        fig = go.Figure()
        
        # Add pie chart
        fig.add_trace(go.Pie(
            labels=['PROD', 'NON-PROD'],
            values=[prod_costs, nonprod_costs],
            hole=0.4,
            marker=dict(colors=['#3366cc', '#33aa33']),
            text=[f"{prod_pct:.1f}%", f"{nonprod_pct:.1f}%"],
            textinfo='value+percent',
            hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>',
            insidetextorientation='radial'
        ))
        
        # Update layout
        fig.update_layout(
            title="Cost Breakdown by Environment",
            title_x=0.5,
            height=450,
            margin=dict(l=50, r=50, t=80, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            ),
            annotations=[
                dict(
                    text=f"Total: ${total_cost:,.2f}",
                    x=0.5, y=0.5,
                    font=dict(size=16, color='#333'),
                    showarrow=False
                )
            ],
            plot_bgcolor='rgba(245,247,249,0.8)',
            paper_bgcolor='rgba(245,247,249,0.8)',
            font=dict(
                family="Segoe UI, Arial, sans-serif"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Segoe UI, Arial, sans-serif"
            )
        )
        
        # Removed interactivity for environment chart (no longer needed)
        # fig.update_layout(
        #     updatemenus=[
        #         dict(
        #             type="buttons",
        #             direction="right",
        #             x=0.01,
        #             y=1.15,
        #             buttons=[
        #                 dict(
        #                     label="Pie Chart",
        #                     method="update",
        #                     args=[{
        #                         "type": "pie",
        #                         "hole": 0.4,
        #                         "textinfo": "value+percent"
        #                     }]
        #                 ),
        #                 dict(
        #                     label="Bar Chart",
        #                     method="update",
        #                     args=[{
        #                         "type": "bar",
        #                         "hole": None,
        #                         "textinfo": None,
        #                         "orientation": "v",
        #                         "text": [f"${prod_costs:,.2f} ({prod_pct:.1f}%)", f"${nonprod_costs:,.2f} ({nonprod_pct:.1f}%)"],
        #                         "textposition": "auto"
        #                     }, {
        #                         "xaxis": {"title": "Environment"},
        #                         "yaxis": {"title": "Cost ($)", "tickprefix": "$"},
        #                         "annotations": []
        #                     }]
        #                 )
        #             ]
        #         )
        #     ]
        # )
        
        # Convert to JSON
        return json.dumps(fig, cls=PlotlyJSONEncoder)
        
    except Exception as e:
        logger.error(f"Error creating interactive environment breakdown chart: {e}")
        # Return a minimal valid JSON if there's an error
        return json.dumps({"data": [], "layout": {"title": "Error creating chart"}})


def get_project_dataset_config(project_id: str, dataset: str) -> Dict[str, Any]:
    """
    Get configuration for a specific project and dataset.
    
    Args:
        project_id: Google Cloud project ID
        dataset: BigQuery dataset name
        
    Returns:
        Dictionary with project and dataset configuration
    """
    return {
        'project_id': project_id,
        'dataset': dataset
    }