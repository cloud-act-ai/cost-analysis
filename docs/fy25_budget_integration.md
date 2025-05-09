# FY25 Budget Integration Guide

This document provides step-by-step instructions for integrating FY25 budget data from a new table into the FinOps360 Cost Analysis Dashboard.

## Prerequisites

- Ensure the new budget table exists in your BigQuery dataset
- The budget table should contain at least columns for environment type and budget amount

## Integration Steps

### 1. Update SQL Query File

Create a new SQL file in the `/app/sql/` directory:

```bash
touch /app/sql/fy25_budget.sql
```

Add your SQL query to retrieve FY25 budget data. Example structure:

```sql
-- FY25 budget query
SELECT
    environment_type,
    budget_amount
FROM `{project_id}.{dataset}.budget_table`
WHERE fiscal_year = '2025'
GROUP BY environment_type
```

### 2. Update Data Access Module

Modify `/app/data_access.py` to include a new function for retrieving FY25 budget data:

1. Add a new import for the SQL file at the top with other imports
2. Add a new function called `get_fy25_budget` that uses the BigQuery client to execute the query
3. Add appropriate error handling and sample data fallback

### 3. Update Dashboard Generation

Modify `/app/dashboard.py` to include the FY25 budget data:

1. Add a call to the new `get_fy25_budget` function in the `generate_html_report` function
2. Add the budget data to the template data dictionary
3. Add appropriate calculations to compare actual costs against budget

### 4. Update HTML Template

Modify `/app/templates/dashboard_template.html` to display the FY25 budget data:

1. Add a new column or section in the appropriate tables/charts
2. Add percentage indicators for budget vs actual comparison
3. Ensure proper formatting for the budget values (millions, etc.)

### 5. Update Sample Data (Optional)

If you want to provide sample data for testing:

1. Modify `/app/utils/sample_data.py` to include a `create_sample_fy25_budget` function
2. Ensure the sample data structure matches the expected structure from BigQuery

## Testing

1. Run the dashboard with sample data to verify the integration works
2. Check that the budget values are displayed correctly
3. Verify percentage calculations are accurate
4. Ensure proper color coding for over/under budget indicators

## Deployment

1. Update the deployment scripts if necessary
2. Document any new configuration parameters or environment variables needed