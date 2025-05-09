# FinOps360 Troubleshooting Guide

This document provides solutions to common issues that may arise when working with the FinOps360 Cost Analysis Dashboard.

## BigQuery Authentication Issues

**Symptoms:**
- Error messages about authentication
- "Reauthentication is needed"
- Empty data in the dashboard

**Solutions:**
1. Verify the `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly:
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

2. If needed, reauthenticate with:
   ```bash
   gcloud auth application-default login
   ```

3. Check that your service account has the necessary permissions to access the BigQuery data.

## Data Display Issues

**Symptoms:**
- Missing data in charts or tables
- "NaN" or zero values
- Incorrect calculations

**Solutions:**
1. Check if the SQL queries in `app/sql/` are correctly formatted
2. Verify that the column names in the queries match the data in BigQuery
3. Examine the data transformation logic in `app/dashboard.py`
4. Check if the sample data is being used instead of BigQuery data

## Chart Rendering Issues

**Symptoms:**
- Charts not displaying
- JavaScript errors in the browser console
- Missing or incorrect chart elements

**Solutions:**
1. Check that Plotly.js is loaded correctly in the HTML template
2. Verify that the chart configuration in `app/utils/chart_config.py` is correct
3. Look for console errors in the browser
4. Check if the chart data in `app/utils/interactive_charts.py` is properly formatted

## Type Errors

**Symptoms:**
- "unsupported operand type(s) for +: 'int' and 'str'" errors
- Other type-related errors

**Solutions:**
1. Check for type conversions in `app/dashboard.py` and `app/utils/interactive_charts.py`
2. Ensure numeric columns are properly converted with `pd.to_numeric()`
3. Use appropriate data type handling for dates and times

## Missing Files or Directories

**Symptoms:**
- "File not found" errors
- "No such file or directory" errors

**Solutions:**
1. Check that all directories exist and have the correct permissions
2. Verify that the file paths are correct and absolute
3. Create any missing directories before writing files

## Chart Configuration Issues

**Symptoms:**
- Charts with incorrect appearance
- Missing chart elements
- Wrong colors or styles

**Solutions:**
1. Check the chart configuration in `app/utils/chart_config.py`
2. Verify that the chart series definitions match the data columns
3. Test with sample data to isolate the issue

## Performance Issues

**Symptoms:**
- Dashboard generation is slow
- BigQuery queries time out
- High memory usage

**Solutions:**
1. Optimize SQL queries to retrieve only necessary data
2. Add appropriate filters to limit data volume
3. Implement pagination for large datasets
4. Add caching for frequently accessed data

## Data Integration Issues

**Symptoms:**
- Missing data from new sources
- Incorrect data from new sources
- Errors when adding new data sources

**Solutions:**
1. Verify that new SQL queries are correctly formatted
2. Check that the data access functions in `app/data_access.py` are properly implemented
3. Test with sample data before integrating with BigQuery
4. Check for column name mismatches or type incompatibilities

## Report Generation Issues

**Symptoms:**
- Empty or incomplete HTML reports
- Missing sections in the dashboard
- Template rendering errors

**Solutions:**
1. Check the template in `app/templates/dashboard_template.html`
2. Verify that all template variables are properly passed in `app/dashboard.py`
3. Look for syntax errors in the Jinja2 template
4. Ensure the output directory exists and is writable