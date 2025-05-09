"""
Interactive chart utilities for FinOps360 cost analysis dashboard.
"""
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.utils import PlotlyJSONEncoder
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from app.utils.chart_config import (
    get_chart_config,
    is_chart_enabled,
    are_charts_enabled,
    get_chart_dimensions,
    get_chart_colors,
)

logger = logging.getLogger(__name__)

def create_interactive_daily_trend_chart(df: pd.DataFrame) -> str:
    """
    Create an interactive daily trend chart with separate styling for forecasted costs.

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

        # Get unique environments
        environments = df['environment_type'].unique()
        print(f"Debug - Found environments: {environments}")

        # Get today's date (3 days ago to match dashboard logic)
        today = datetime.now().date() - timedelta(days=3)

        # Check if NON-PROD is in the data
        has_nonprod = 'NON-PROD' in environments
        has_prod = 'PROD' in environments
        print(f"Debug - Has PROD: {has_prod}, Has NON-PROD: {has_nonprod}")

        # Force both environments to be included
        if not has_nonprod or not has_prod:
            # Get sample data for the missing environment
            from app.utils.sample_data import create_sample_daily_trend_data
            sample_data = create_sample_daily_trend_data()

            # Update our environments list to include both
            if not has_nonprod:
                print("Debug - Adding missing NON-PROD data")
                nonprod_data = sample_data[sample_data['environment_type'] == 'NON-PROD']
                df = pd.concat([df, nonprod_data], ignore_index=True)
                environments = df['environment_type'].unique()

            if not has_prod:
                print("Debug - Adding missing PROD data")
                prod_data = sample_data[sample_data['environment_type'] == 'PROD']
                df = pd.concat([df, prod_data], ignore_index=True)
                environments = df['environment_type'].unique()

            print(f"Debug - Updated environments: {environments}")

        # Process each environment type
        for env in environments:
            print(f"Debug - Processing environment: {env}")
            env_data = df[df['environment_type'] == env]
            print(f"Debug - {env} data rows: {len(env_data)}")

            # Only use actual data - no forecast
            actual_data = env_data[pd.to_datetime(env_data['date']).dt.date <= today]
            print(f"Debug - {env} actual data rows: {len(actual_data)}")

            # Line color based on environment
            color = prod_color if env == 'PROD' else nonprod_color

            # Add actual daily cost line
            if not actual_data.empty:
                fig.add_trace(go.Scatter(
                    x=actual_data['date'],
                    y=actual_data['daily_cost'],
                    mode='lines',
                    name=f"{env} Daily Cost",
                    line=dict(color=color, width=2.5, shape='spline', smoothing=0.3),
                    hovertemplate='%{x|%b %d, %Y}: $%{y:,.2f}<extra></extra>'
                ))
                print(f"Debug - Added trace for {env}")
        
        # Update layout
        fig.update_layout(
            title="FY26 Daily Cost for PROD and NON-PROD",
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

        # Make the figure responsive
        fig.update_layout(
            autosize=True,
            legend_title_text="",
            legend_title_font_size=10
        )

        # No vertical line or forecast annotation needed - only showing actual data

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
                x=float(row.prod_ytd_cost),
                y=row.product_name,
                text=f" ${float(row.prod_ytd_cost):,.2f}",
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
                x=float(row.prod_ytd_cost),
                y=row.cto_org,
                text=f" ${float(row.prod_ytd_cost):,.2f}",
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
                x=float(row.prod_ytd_cost),
                y=row.pillar_name,
                text=f" ${float(row.prod_ytd_cost):,.2f} ({int(product_count)} products)",
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


# New enhanced chart functions based on chart_config.py

def create_enhanced_daily_trend_chart(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Create an enhanced interactive time series chart for daily cost trends.

    Args:
        data: DataFrame with daily trend data

    Returns:
        Dictionary with chart HTML and JSON data
    """
    if not are_charts_enabled() or not is_chart_enabled("daily_trend"):
        return {"html": "", "json_data": "{}"}

    if data.empty:
        return {"html": "<!-- No data available for daily trend chart -->", "json_data": "{}"}

    # Get chart configuration
    chart_config = get_chart_config("daily_trend")
    dimensions = get_chart_dimensions()

    # Create the figure
    fig = go.Figure()

    # Add supplementary columns to match chart configuration if they don't exist
    if 'fy26_avg_daily_spend' not in data.columns and 'daily_cost' in data.columns:
        # Create a groupby to calculate averages by environment
        avg_costs = data.groupby('environment_type')['daily_cost'].mean().reset_index()
        # Create a mapping dictionary
        avg_mapping = dict(zip(avg_costs['environment_type'], avg_costs['daily_cost']))
        # Add baseline columns as constants based on environment
        data['fy26_avg_daily_spend'] = data['environment_type'].map(
            lambda x: avg_mapping.get(x, 0) if x in avg_mapping else 0
        )
        data['fy25_avg_daily_spend'] = data['environment_type'].map(
            lambda x: avg_mapping.get(x, 0) * 0.8 if x in avg_mapping else 0
        )

    # No forecast columns needed

    # Get today's date (3 days ago to match dashboard logic)
    today = datetime.now().date() - timedelta(days=3)

    # Process each series from configuration
    for series_config in chart_config.get("series", []):
        series_name = series_config.get("name", "")
        column = series_config.get("column", "")
        filter_by = series_config.get("filter", {})
        color = series_config.get("color", "#000000")
        line_type = series_config.get("type", "line")
        dash_style = series_config.get("dash", "solid")

        # Filter data for this series
        series_data = data.copy()

        # Ensure numeric types for all numeric columns
        if 'daily_cost' in series_data.columns:
            series_data['daily_cost'] = pd.to_numeric(series_data['daily_cost'], errors='coerce').fillna(0)

        # Convert all possible columns to numeric to avoid type errors
        for col in series_data.columns:
            if col != 'date' and col != 'environment_type':
                try:
                    series_data[col] = pd.to_numeric(series_data[col], errors='coerce').fillna(0)
                except Exception:
                    pass  # Skip columns that can't be converted

        # Filter data based on configuration
        for key, value in filter_by.items():
            if key in series_data.columns:
                if series_data[key].dtype == 'object':
                    # Case-insensitive comparison for environment_type
                    if key == 'environment_type':
                        series_data = series_data[series_data[key].str.upper() == value.upper()]
                    else:
                        series_data = series_data[series_data[key].str.lower() == value.lower()]
                else:
                    series_data = series_data[series_data[key] == value]

        if column in series_data.columns and not series_data.empty:
            # Ensure the y-axis data is numeric
            series_data[column] = pd.to_numeric(series_data[column], errors='coerce').fillna(0)

            # Split into actual and forecast data
            series_data['date'] = pd.to_datetime(series_data['date'])
            actual_data = series_data[series_data['date'].dt.date <= today]
            forecast_data = series_data[series_data['date'].dt.date > today]

            # Add actual data trace
            if not actual_data.empty:
                fig.add_trace(go.Scatter(
                    x=actual_data['date'],
                    y=actual_data[column],
                    mode='lines',
                    name=f"{series_name} (Actual)",
                    line=dict(color=color, dash=dash_style),
                    hovertemplate='%{x|%b %d, %Y}: $%{y:,.2f} (Actual)<extra></extra>'
                ))

            # Add forecast data with dotted line style
            if not forecast_data.empty:
                fig.add_trace(go.Scatter(
                    x=forecast_data['date'],
                    y=forecast_data[column],
                    mode='lines',
                    name=f"{series_name} (Forecast)",
                    line=dict(color=color, dash='dash'),  # Always use dotted line for forecast data
                    hovertemplate='%{x|%b %d, %Y}: $%{y:,.2f} (Forecast)<extra></extra>'
                ))
    
    # Add vertical line at today's date to separate actual vs forecast data
    fig.add_shape(
        type="line",
        x0=today,
        y0=0,
        x1=today,
        y1=1,
        yref="paper",
        line=dict(
            color="rgba(169, 169, 169, 0.5)",
            width=2,
            dash="dot",
        ),
    )

    # Add annotation to indicate forecast start
    fig.add_annotation(
        x=today,
        y=1,
        yref="paper",
        text="Forecast →",
        showarrow=False,
        xanchor="left",
        bgcolor="rgba(255, 255, 255, 0.7)",
        bordercolor="rgba(169, 169, 169, 0.5)",
        borderwidth=1,
        borderpad=4,
        font=dict(size=10)
    )
    
    # Configure axes
    x_axis_config = chart_config.get("x_axis", {})
    y_axis_config = chart_config.get("y_axis", {})
    
    # Set axis ranges if specified
    x_range = x_axis_config.get("range")
    if x_range:
        fig.update_xaxes(range=x_range)
    
    # Set y-axis to start at zero if specified
    if y_axis_config.get("start_at_zero", False):
        fig.update_yaxes(rangemode="tozero")
    
    # Format y-axis as currency if specified
    if y_axis_config.get("format") == "currency":
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    
    # Set axis titles
    fig.update_xaxes(title_text=x_axis_config.get("title", ""))
    fig.update_yaxes(title_text=y_axis_config.get("title", ""))
    
    # Set chart layout without title and buttons
    fig.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=dimensions["height"],
        margin=dict(l=50, r=50, t=50, b=50),  # Reduced top margin since no title
        hovermode="x unified",
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
    
    # Generate HTML and JSON data
    html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    json_data = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return {"html": html, "json_data": json_data}

def create_enhanced_stacked_bar_chart(
    data: pd.DataFrame,
    chart_key: str
) -> Dict[str, Any]:
    """
    Create an enhanced stacked bar chart for cost comparisons.

    Args:
        data: DataFrame with cost data
        chart_key: Key identifying the chart type (cto_costs, pillar_costs, product_costs)

    Returns:
        Dictionary with chart HTML and JSON data
    """
    # Get display_millions configuration
    from app.utils.config import load_config
    config = load_config("config.yaml")
    display_millions = config.get('data', {}).get('display_millions', True)
    if not are_charts_enabled() or not is_chart_enabled(chart_key):
        return {"html": "", "json_data": "{}"}

    if data.empty:
        return {"html": f"<!-- No data available for {chart_key} chart -->", "json_data": "{}"}

    # Get chart configuration
    chart_config = get_chart_config(chart_key)
    dimensions = get_chart_dimensions()
    colors = get_chart_colors()

    # Ensure all columns are the right data type first
    # Convert all data columns to numeric to prevent type errors
    for column in data.columns:
        if column not in ['environment_type', 'cto_org', 'pillar_name', 'product_id', 'product_name', 'display_id']:
            data[column] = pd.to_numeric(data[column], errors='coerce').fillna(0)

    # Sort data if specified
    sort_config = chart_config.get("sort_by", {})
    if sort_config:
        sort_column = sort_config.get("column")
        sort_direction = sort_config.get("direction", "ascending")
        if sort_column and sort_column in data.columns:
            is_ascending = sort_direction.lower() != "descending"
            data = data.sort_values(by=sort_column, ascending=is_ascending)

    # Limit number of items if specified
    limit = chart_config.get("limit")
    if limit and limit > 0:
        data = data.head(limit)

    # Create the figure
    fig = go.Figure()

    # Check chart type for orientation
    is_horizontal = "horizontal" in chart_config.get("type", "")

    # Get axis column configuration
    y_axis_column = chart_config.get("y_axis", {}).get("column", "")
    if not y_axis_column or y_axis_column not in data.columns:
        return {"html": f"<!-- Missing y-axis column for {chart_key} chart -->", "json_data": "{}"}

    # Sort data to ensure consistent display order
    data = data.sort_values(by="total_ytd_cost", ascending=True)  # Ascending for better horizontal display

    # Map display names to appropriate column names based on chart type
    display_column = y_axis_column
    if chart_key == "product_costs" and "product_id" in data.columns:
        display_column = "product_id"

    y_values = data[display_column].tolist()

    # Calculate total for percentages - ensure numeric types
    data['prod_ytd_cost'] = pd.to_numeric(data['prod_ytd_cost'], errors='coerce').fillna(0)
    data['nonprod_ytd_cost'] = pd.to_numeric(data['nonprod_ytd_cost'], errors='coerce').fillna(0)
    data['total_for_pct'] = data['prod_ytd_cost'] + data['nonprod_ytd_cost']
    
    # Add series for horizontal bar chart
    for series_config in chart_config.get("series", []):
        series_name = series_config.get("name", "")
        column = series_config.get("column", "")
        color = series_config.get("color", "#000000")
        show_percentage = series_config.get("show_percentage", False)
        
        if column in data.columns:
            # Ensure column data is numeric
            data[column] = pd.to_numeric(data[column], errors='coerce').fillna(0)
            
            # Calculate percentages if needed
            text = None
            if show_percentage:
                percentages = (data[column] / data['total_for_pct'] * 100).fillna(0).round(1)
                # Ensure all values are converted to float before formatting
                formatted_text = []
                for val, pct in zip(data[column], percentages):
                    try:
                        val_float = float(val)
                        pct_float = float(pct)
                        if display_millions:
                            formatted_text.append(f"${val_float/1000000:.2f}M ({pct_float:.1f}%)")
                        else:
                            formatted_text.append(f"${val_float:.0f} ({pct_float:.1f}%)")
                    except (ValueError, TypeError):
                        # Fallback for any conversion errors
                        formatted_text.append("")
                text = formatted_text
            
            # Convert x values to list of floats
            x_values = []
            for val in data[column].values:
                try:
                    x_values.append(float(val))
                except (ValueError, TypeError):
                    x_values.append(0.0)

            # Determine hover template based on display_millions setting
            if display_millions:
                hover_template = '<b>%{y}</b><br>%{fullData.name}: $%{x:,.2f}M<extra></extra>'
                x_values = [x/1000000 for x in x_values]  # Convert to millions
            else:
                hover_template = '<b>%{y}</b><br>%{fullData.name}: $%{x:,.0f}<extra></extra>'

            fig.add_trace(go.Bar(
                y=y_values,
                x=x_values,
                name=series_name,
                marker_color=color,
                orientation='h',
                text=text,
                textposition='inside',
                insidetextanchor='middle',
                hovertemplate=hover_template
            ))
    
    # Configure axes
    x_axis_config = chart_config.get("x_axis", {})
    y_axis_config = chart_config.get("y_axis", {})
    
    # Set x-axis to start at zero if specified
    if x_axis_config.get("start_at_zero", False):
        fig.update_xaxes(rangemode="tozero")
    
    # Format x-axis as currency if specified
    if x_axis_config.get("format") == "currency":
        if display_millions:
            fig.update_xaxes(tickprefix="$", tickformat=",.2f", title=x_axis_config.get("title", "") + " (Millions)")
        else:
            fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    
    # Set axis titles
    fig.update_xaxes(title_text=x_axis_config.get("title", ""))
    fig.update_yaxes(title_text=y_axis_config.get("title", ""))
    
    # Configure for stacked bar chart
    fig.update_layout(
        barmode="stack",
        title=chart_config.get("title", "Cost Comparison"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=dimensions["height"],
        margin=dict(l=100, r=50, t=80, b=50),  # More left margin for labels
        hovermode="closest",
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
    
    # Generate HTML and JSON data
    html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    json_data = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return {"html": html, "json_data": json_data}

def create_enhanced_cto_costs_chart(data: pd.DataFrame) -> Dict[str, Any]:
    """Generate enhanced stacked bar chart for CTO organization costs."""
    return create_enhanced_stacked_bar_chart(data, "cto_costs")

def create_enhanced_pillar_costs_chart(data: pd.DataFrame) -> Dict[str, Any]:
    """Generate enhanced stacked bar chart for pillar team costs."""
    return create_enhanced_stacked_bar_chart(data, "pillar_costs")

def create_enhanced_product_costs_chart(data: pd.DataFrame) -> Dict[str, Any]:
    """Generate enhanced stacked bar chart for product costs."""
    return create_enhanced_stacked_bar_chart(data, "product_costs")

def generate_all_enhanced_charts(
    daily_trend_data: pd.DataFrame,
    cto_costs: List[Dict[str, Any]],
    pillar_costs: List[Dict[str, Any]],
    product_costs: List[Dict[str, Any]],
    use_enhanced_charts: bool = True
) -> Dict[str, Dict[str, Any]]:
    """
    Generate all enhanced charts for the dashboard.
    
    Args:
        daily_trend_data: DataFrame with daily trend data
        cto_costs: List of CTO cost data
        pillar_costs: List of pillar cost data
        product_costs: List of product cost data
        use_enhanced_charts: Whether to use the enhanced charts from chart_config
        
    Returns:
        Dictionary with all chart data
    """
    if not are_charts_enabled():
        return {}
    
    # Convert list data to DataFrames
    cto_df = pd.DataFrame(cto_costs) if cto_costs else pd.DataFrame()
    pillar_df = pd.DataFrame(pillar_costs) if pillar_costs else pd.DataFrame()
    product_df = pd.DataFrame(product_costs) if product_costs else pd.DataFrame()
    
    # Generate all charts
    if use_enhanced_charts:
        charts = {
            "daily_trend": create_enhanced_daily_trend_chart(daily_trend_data),
            "cto_costs": create_enhanced_cto_costs_chart(cto_df),
            "pillar_costs": create_enhanced_pillar_costs_chart(pillar_df),
            "product_costs": create_enhanced_product_costs_chart(product_df),
        }
    else:
        # Use the original chart functions
        charts = {
            "daily_trend": {"json_data": create_interactive_daily_trend_chart(daily_trend_data)},
            "cto_costs": {"json_data": create_interactive_cto_breakdown_chart(cto_df)},
            "pillar_costs": {"json_data": create_interactive_pillar_breakdown_chart(pillar_df)},
            "product_costs": {"json_data": create_interactive_product_breakdown_chart(product_df)},
        }
    
    return charts