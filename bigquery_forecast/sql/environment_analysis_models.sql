-- Environment Analysis - Create Time Series Models
-- Creates a separate model for each environment

-- Dev Environment Model
CREATE OR REPLACE MODEL `finops360-dev-2025.test.env_dev_model`
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='date',
  time_series_data_col='total_cost',
  time_series_id_col=['tr_product_pillar_team', 'service_name'],
  auto_arima=TRUE,
  data_frequency='DAILY',
  holiday_region='US'
) AS
SELECT 
  date,
  tr_product_pillar_team,
  service_name,
  SUM(cost) as total_cost
FROM 
  `finops360-dev-2025.test.cost_analysis_test`
WHERE 
  date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY) AND CURRENT_DATE()
  AND LOWER(environment) LIKE '%dev%'
GROUP BY 
  date, tr_product_pillar_team, service_name
ORDER BY 
  date;

-- Prod Environment Model
CREATE OR REPLACE MODEL `finops360-dev-2025.test.env_prod_model`
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='date',
  time_series_data_col='total_cost',
  time_series_id_col=['tr_product_pillar_team', 'service_name'],
  auto_arima=TRUE,
  data_frequency='DAILY',
  holiday_region='US'
) AS
SELECT 
  date,
  tr_product_pillar_team,
  service_name,
  SUM(cost) as total_cost
FROM 
  `finops360-dev-2025.test.cost_analysis_test`
WHERE 
  date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY) AND CURRENT_DATE()
  AND LOWER(environment) LIKE '%prod%'
GROUP BY 
  date, tr_product_pillar_team, service_name
ORDER BY 
  date;

-- Stage/Test Environment Model
CREATE OR REPLACE MODEL `finops360-dev-2025.test.env_test_model`
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='date',
  time_series_data_col='total_cost',
  time_series_id_col=['tr_product_pillar_team', 'service_name'],
  auto_arima=TRUE,
  data_frequency='DAILY',
  holiday_region='US'
) AS
SELECT 
  date,
  tr_product_pillar_team,
  service_name,
  SUM(cost) as total_cost
FROM 
  `finops360-dev-2025.test.cost_analysis_test`
WHERE 
  date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY) AND CURRENT_DATE()
  AND (LOWER(environment) LIKE '%stage%' OR LOWER(environment) LIKE '%test%' OR LOWER(environment) LIKE '%qa%')
GROUP BY 
  date, tr_product_pillar_team, service_name
ORDER BY 
  date;