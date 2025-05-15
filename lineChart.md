# FY26 Daily Cost Line Chart Documentation

This document provides documentation for the daily cost trend line chart that shows PROD and NON-PROD environment costs over time.

## Overview

The "FY26 Daily Cost for PROD and NON-PROD" chart displays daily spending trends across the fiscal year. It shows actual spending up to the current date and forecast spending for the remainder of the fiscal year. This chart helps users visualize daily fluctuations in spending and identify trends across environments.

## Data Source

The chart uses data from the `avg_daily_cost_table` in BigQuery, fetched via the following SQL query:

```sql
-- Daily trend data query
SELECT
    date,
    CASE
        WHEN environment_type LIKE 'PROD%' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    daily_cost
FROM `{project_id}.{dataset}.{avg_table}`
WHERE date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY date, environment_type
```

## Implementation

### Data Flow

1. The data is fetched using `get_daily_trend_data_async()` in `app/core/data_access.py`
2. Chart generation occurs in `create_enhanced_daily_trend_chart()` in `app/utils/chart/generator.py`
3. Chart configuration is defined in `app/utils/chart/config.py`
4. The chart is rendered in the template using Plotly.js

### Chart Configuration

The chart has the following configuration:

```javascript
{
    "enabled": true,
    "type": "time_series",
    "title": "Daily Cost Analysis for PROD and NON-PROD Environments",
    "x_axis": {
        "title": "Date",
        "range": ["2025-02-01", "2026-01-31"],  // Feb 2025 to Jan 2026
        "forecast_date": "current_date",  // Mark forecast line at current date
    },
    "y_axis": {
        "title": "Daily Cost ($)",
        "start_at_zero": true,
        "format": "currency",  // Format as currency
    },
    "series": [
        {
            "name": "PROD Daily Cost (FY26)",
            "column": "daily_cost",
            "filter": {"environment_type": "PROD"},
            "color": "#3498db",  // Blue
            "type": "line",
        },
        {
            "name": "NON-PROD Daily Cost (FY26)",
            "column": "daily_cost",
            "filter": {"environment_type": "NON-PROD"},
            "color": "#2ecc71",  // Green
            "type": "line",
        },
        {
            "name": "FY26 Avg Daily Spend",
            "column": "fy26_avg_daily_spend",
            "filter": {"environment_type": "PROD"},
            "color": "#95a5a6",  // Gray
            "type": "line",
            "dash": "dash",
        },
        {
            "name": "FY25 Avg Daily Spend",
            "column": "fy25_avg_daily_spend",
            "filter": {"environment_type": "PROD"},
            "color": "#e74c3c",  // Red
            "type": "line",
            "dash": "dash",
        }
    ],
    "annotations": [
        {
            "type": "vline",
            "x": "current_date",
            "line": {"color": "#e74c3c", "dash": "dash"},
            "annotation_text": "Current Date",
        }
    ]
}
```

### Chart Generation Logic

The chart generation process:

1. Fetches daily cost data for PROD and NON-PROD environments
2. Adds calculated columns for average daily spend
3. Splits the data into actual and forecast sections, with different styling
4. Adds a vertical line to separate actual and forecast data
5. Configures axes, legends, and tooltips
6. Renders using Plotly.js

### Key Features

- Blue line for PROD environment costs
- Green line for NON-PROD environment costs
- Dotted gray line for average FY26 daily spend (reference)
- Dotted red line for average FY25 daily spend (reference)
- Vertical divider between actual and forecast data
- Currency formatted Y-axis
- Interactive tooltips showing exact cost values
- Responsive design that adapts to container width

## HTML Template Integration

To include this chart in a custom template, use the following code:

```html
<div class="chart-section">
    <div class="chart-container full-width">
        <h2>FY26 Daily Cost for PROD and NON-PROD</h2>
        <div id="daily_trend_chart" class="chart">
            {{ daily_trend_chart.html|safe }}
        </div>
    </div>
</div>
```

## JavaScript Initialization

The chart is initialized with Plotly.js:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    try {
        const dailyTrendData = JSON.parse('{{ daily_trend_chart.json_data|safe }}');
        Plotly.newPlot('daily_trend_chart', dailyTrendData.data, dailyTrendData.layout);
    } catch (e) {
        console.error('Error initializing daily trend chart:', e);
    }
    
    // Make chart responsive
    window.addEventListener('resize', function() {
        Plotly.relayout('daily_trend_chart', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    });
});
```

## CSS Styling

The chart uses the following CSS classes:

```css
.chart-section {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 20px;
}
.chart-container {
    background-color: #fff;
    border-radius: 5px;
    padding: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    flex: 1;
    min-width: 45%;
}
.chart-container.full-width {
    width: 100%;
    flex-basis: 100%;
}
.chart-container h2 {
    margin-top: 0;
    font-size: 18px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
    text-align: center;
}
.chart {
    width: 100%;
    height: auto;
    max-height: 500px;
}
```

## Disabling the Chart

To disable this chart, set the `enabled` property to `false` in the `daily_trend` section of the chart configuration in `app/utils/chart/config.py`.