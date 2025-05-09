# Daily Cost Chart Editing Guide

This document provides instructions for editing, adding, or removing lines from the "FY26 Daily Cost for PROD and NON-PROD (Including Forecast)" chart in the FinOps360 Cost Analysis Dashboard.

## Chart Overview

The daily cost chart is generated in the `/app/utils/interactive_charts.py` file, specifically in the `create_enhanced_daily_trend_chart` function. This chart displays daily costs for PROD and NON-PROD environments, including both actual and forecasted data.

## Editing Chart Data Series

### Adding a New Line

To add a new data series (line) to the chart:

1. Open `/app/utils/chart_config.py`
2. Locate the `CHART_CONFIGS` dictionary and the `"daily_trend"` section
3. In the `"series"` list, add a new entry following this template:

```python
{
    "name": "Your New Line Name",
    "column": "column_name_in_dataframe",  # Existing column or one you'll create
    "filter": {"environment_type": "ENVIRONMENT_TYPE"},  # Optional filter
    "color": "#HEXCOLOR",  # Use a color from CHART_COLORS or define new one
    "type": "line",        # Can be 'line', 'bar', 'scatter', etc.
    "dash": "dash",        # Optional: 'dash', 'dot', 'dashdot', or 'solid'
}
```

4. If your new line requires a new calculated column, you'll need to add the calculation in the `create_enhanced_daily_trend_chart` function in `/app/utils/interactive_charts.py`

### Removing a Line

To remove an existing line from the chart:

1. Open `/app/utils/chart_config.py`
2. Locate the `CHART_CONFIGS` dictionary and the `"daily_trend"` section
3. In the `"series"` list, remove the dictionary entry for the line you want to remove

### Modifying an Existing Line

To change the appearance or behavior of an existing line:

1. Open `/app/utils/chart_config.py`
2. Locate the `CHART_CONFIGS` dictionary and the `"daily_trend"` section
3. In the `"series"` list, find the entry for the line you want to modify
4. Update any of these properties:
   - `"name"`: Changes the label in the legend
   - `"color"`: Changes the line color
   - `"dash"`: Changes line style ('solid', 'dash', 'dot', 'dashdot')
   - `"width"`: Changes line thickness (default is 2)
   - `"filter"`: Changes which subset of data is used
   - `"type"`: Changes visualization type ('line', 'bar', etc.)

## Adding Forecast Data

To modify how forecast data is generated:

1. Open `/app/utils/interactive_charts.py`
2. Locate the `create_enhanced_daily_trend_chart` function
3. Find the section that begins with `# Create more sophisticated forecast columns if they don't exist`
4. Modify the forecasting logic as needed

Key components of the forecast generation:

- The cutoff date (currently set to March 15th, 2025) determines where actual data ends and forecast begins
- Different forecast methods can be applied (linear, seasonal, etc.)
- You can add different forecast types for different environment types

## Customizing Chart Appearance

To modify the overall chart appearance:

1. Open `/app/utils/chart_config.py`
2. Locate the `CHART_CONFIGS` dictionary and the `"daily_trend"` section
3. Update the `"layout"` section to change:
   - Title: `"title": {"text": "Your New Title"}`
   - Axes: `"xaxis"` or `"yaxis"` settings
   - Legend: `"legend"` settings
   - Height: `"height": 600` (in pixels)
   - Colors: Add or modify entries in the `CHART_COLORS` dictionary

## Testing Your Changes

After making changes:

1. Run the dashboard with `python -m app.main` or `./run.sh`
2. Check the generated dashboard in the reports directory
3. Verify that your changes to the chart appear as expected

## Common Issues and Solutions

- **Missing data**: Ensure the data column exists in the DataFrame
- **Line not appearing**: Check that filters match your data values
- **Forecast not showing**: Verify the cutoff date is appropriate
- **Color conflicts**: Use distinct colors for better readability
- **Performance issues**: Limit the number of data points or series for better performance