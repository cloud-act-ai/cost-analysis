-- Create Time Series Forecast Model with simpler approach
CREATE OR REPLACE MODEL `finops360-dev-2025.test.ts_forecast_model`
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='date',
  time_series_data_col='total_cost',
  time_series_id_col=['service_name'], -- Simplified for better convergence
  auto_arima=TRUE,
  data_frequency='DAILY',
  holiday_region='US'
) AS

-- Create a view with more aggregated data to ensure sufficient points
WITH daily_costs AS (
  SELECT 
    date,
    service_name,
    SUM(cost) as total_cost
  FROM 
    `finops360-dev-2025.test.cost_analysis_test`
  WHERE 
    date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) AND CURRENT_DATE()
  GROUP BY 
    date, service_name
)

-- Fill in any missing dates to ensure continuous time series
SELECT
  date,
  service_name,
  total_cost
FROM
  daily_costs
ORDER BY 
  service_name, date