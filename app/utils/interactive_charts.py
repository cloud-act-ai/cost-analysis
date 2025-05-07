"""
Interactive chart utilities for FinOps360 cost analysis dashboard.
"""
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
from typing import Dict, Any, List, Optional

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
        
        # Define colors
        prod_color = '#3366cc'  # Blue for PROD
        nonprod_color = '#33aa33'  # Green for NON-PROD
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
                line=dict(color=color, width=2),
                hovertemplate='%{x|%b %d, %Y}: $%{y:,.2f}<extra></extra>'
            ))
            
            # Add FY25 average line (dashed)
            fig.add_trace(go.Scatter(
                x=env_data['date'],
                y=env_data['fy25_avg_daily_spend'],
                mode='lines',
                name="FY25 Avg Daily Spend",
                line=dict(color='#999999', width=1, dash='dash'),
                hovertemplate='FY25 Avg: $%{y:,.2f}<extra></extra>'
            ))
            
            # Add FY26 YTD average line (dash-dot)
            fig.add_trace(go.Scatter(
                x=env_data['date'],
                y=env_data['fy26_ytd_avg_daily_spend'],
                mode='lines',
                name="FY26 Avg Daily Spend",
                line=dict(color=avg_color, width=1, dash='dashdot'),
                hovertemplate='FY26 Avg: $%{y:,.2f}<extra></extra>'
            ))
            
            # Add forecasted line (dotted)
            fig.add_trace(go.Scatter(
                x=env_data['date'],
                y=env_data['fy26_forecasted_avg_daily_spend'],
                mode='lines',
                name=f"{env} Forecasted Daily Cost (FY26)",
                line=dict(color=forecast_color, width=2, dash='dot'),
                hovertemplate='Forecast: $%{y:,.2f}<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title="FY26 Daily Cost for PROD and NON-PROD (Including Forecast)",
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
            margin=dict(l=50, r=50, t=80, b=50),
            height=500,
            yaxis=dict(
                tickprefix="$",
                separatethousands=True
            ),
            xaxis=dict(
                tickformat="%b %Y",
                tickangle=-45
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
        
        # Add grid lines
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211,211,211,0.5)'
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(211,211,211,0.5)'
        )
        
        # Make the figure responsive
        fig.update_layout(
            autosize=True,
            legend_title_text="",
            legend_title_font_size=10
        )
        
        # Add interactive features
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.01,
                    y=1.15,
                    buttons=[
                        dict(
                            label="All",
                            method="update",
                            args=[{"visible": [True] * len(fig.data)}]
                        ),
                        dict(
                            label="PROD Only",
                            method="update",
                            args=[{"visible": [True if "PROD" in trace.name and "NON-PROD" not in trace.name else False 
                                               for trace in fig.data]}]
                        ),
                        dict(
                            label="NON-PROD Only",
                            method="update",
                            args=[{"visible": [True if "NON-PROD" in trace.name else False 
                                               for trace in fig.data]}]
                        ),
                        dict(
                            label="Actual Only",
                            method="update",
                            args=[{"visible": [True if "Forecasted" not in trace.name and "Avg" not in trace.name else False 
                                               for trace in fig.data]}]
                        ),
                        dict(
                            label="With Forecasts",
                            method="update",
                            args=[{"visible": [True if "Avg" not in trace.name else False 
                                               for trace in fig.data]}]
                        )
                    ]
                )
            ]
        )
        
        # Convert to JSON
        plotly_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        return plotly_json
        
    except Exception as e:
        logger.error(f"Error creating interactive daily trend chart: {e}")
        # Return a minimal valid JSON if there's an error
        return json.dumps({"data": [], "layout": {"title": "Error creating chart"}})