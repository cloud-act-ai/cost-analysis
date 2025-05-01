-- Environment Cost Forecasting
-- Forecasts costs across different environments

-- Step 1: Production Forecast
CREATE OR REPLACE TABLE `finops360-dev-2025.test.prod_forecast` AS
SELECT
  forecast_timestamp AS forecast_date,
  tr_product_pillar_team,
  service_name,
  forecast_value AS forecasted_cost,
  prediction_interval_lower_bound AS min_cost,
  prediction_interval_upper_bound AS max_cost,
  SAFE_DIVIDE(prediction_interval_upper_bound - prediction_interval_lower_bound, forecast_value) * 100 AS uncertainty_pct
FROM
  ML.FORECAST(MODEL `finops360-dev-2025.test.env_prod_model`,
              STRUCT(30 AS horizon, 0.9 AS confidence_level));

-- Step 2: Development Forecast
CREATE OR REPLACE TABLE `finops360-dev-2025.test.dev_forecast` AS
SELECT
  forecast_timestamp AS forecast_date,
  tr_product_pillar_team,
  service_name,
  forecast_value AS forecasted_cost,
  prediction_interval_lower_bound AS min_cost,
  prediction_interval_upper_bound AS max_cost,
  SAFE_DIVIDE(prediction_interval_upper_bound - prediction_interval_lower_bound, forecast_value) * 100 AS uncertainty_pct
FROM
  ML.FORECAST(MODEL `finops360-dev-2025.test.env_dev_model`,
              STRUCT(30 AS horizon, 0.9 AS confidence_level));

-- Step 3: Test/Stage Forecast
CREATE OR REPLACE TABLE `finops360-dev-2025.test.test_forecast` AS
SELECT
  forecast_timestamp AS forecast_date,
  tr_product_pillar_team,
  service_name,
  forecast_value AS forecasted_cost,
  prediction_interval_lower_bound AS min_cost,
  prediction_interval_upper_bound AS max_cost,
  SAFE_DIVIDE(prediction_interval_upper_bound - prediction_interval_lower_bound, forecast_value) * 100 AS uncertainty_pct
FROM
  ML.FORECAST(MODEL `finops360-dev-2025.test.env_test_model`,
              STRUCT(30 AS horizon, 0.9 AS confidence_level));

-- Step 4: Consolidated forecasts with environment categorization
CREATE OR REPLACE TABLE `finops360-dev-2025.test.env_forecasts_consolidated` AS
SELECT
  forecast_date,
  'Production' AS environment_category,
  tr_product_pillar_team,
  service_name,
  forecasted_cost,
  min_cost,
  max_cost,
  uncertainty_pct,
  
  -- Get current average cost for the category (last 30 days)
  (SELECT AVG(daily_cost)
   FROM `finops360-dev-2025.test.env_daily_costs`
   WHERE LOWER(environment) LIKE '%prod%'
   AND tr_product_pillar_team = p.tr_product_pillar_team
   AND service_name = p.service_name
   AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()) AS current_avg_cost,
   
  -- Calculate projected growth (positive or negative)
  SAFE_DIVIDE(
    forecasted_cost - (SELECT AVG(daily_cost)
                        FROM `finops360-dev-2025.test.env_daily_costs`
                        WHERE LOWER(environment) LIKE '%prod%'
                        AND tr_product_pillar_team = p.tr_product_pillar_team
                        AND service_name = p.service_name
                        AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()),
    (SELECT AVG(daily_cost)
     FROM `finops360-dev-2025.test.env_daily_costs`
     WHERE LOWER(environment) LIKE '%prod%'
     AND tr_product_pillar_team = p.tr_product_pillar_team
     AND service_name = p.service_name
     AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE())
  ) * 100 AS projected_growth_pct
FROM
  `finops360-dev-2025.test.prod_forecast` p

UNION ALL

SELECT
  forecast_date,
  'Development' AS environment_category,
  tr_product_pillar_team,
  service_name,
  forecasted_cost,
  min_cost,
  max_cost,
  uncertainty_pct,
  
  -- Get current average cost for the category (last 30 days)
  (SELECT AVG(daily_cost)
   FROM `finops360-dev-2025.test.env_daily_costs`
   WHERE LOWER(environment) LIKE '%dev%'
   AND tr_product_pillar_team = d.tr_product_pillar_team
   AND service_name = d.service_name
   AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()) AS current_avg_cost,
   
  -- Calculate projected growth (positive or negative)
  SAFE_DIVIDE(
    forecasted_cost - (SELECT AVG(daily_cost)
                        FROM `finops360-dev-2025.test.env_daily_costs`
                        WHERE LOWER(environment) LIKE '%dev%'
                        AND tr_product_pillar_team = d.tr_product_pillar_team
                        AND service_name = d.service_name
                        AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()),
    (SELECT AVG(daily_cost)
     FROM `finops360-dev-2025.test.env_daily_costs`
     WHERE LOWER(environment) LIKE '%dev%'
     AND tr_product_pillar_team = d.tr_product_pillar_team
     AND service_name = d.service_name
     AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE())
  ) * 100 AS projected_growth_pct
FROM
  `finops360-dev-2025.test.dev_forecast` d

UNION ALL

SELECT
  forecast_date,
  'Test/Stage' AS environment_category,
  tr_product_pillar_team,
  service_name,
  forecasted_cost,
  min_cost,
  max_cost,
  uncertainty_pct,
  
  -- Get current average cost for the category (last 30 days)
  (SELECT AVG(daily_cost)
   FROM `finops360-dev-2025.test.env_daily_costs`
   WHERE (LOWER(environment) LIKE '%test%' OR LOWER(environment) LIKE '%stage%' OR LOWER(environment) LIKE '%qa%')
   AND tr_product_pillar_team = t.tr_product_pillar_team
   AND service_name = t.service_name
   AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()) AS current_avg_cost,
   
  -- Calculate projected growth (positive or negative)
  SAFE_DIVIDE(
    forecasted_cost - (SELECT AVG(daily_cost)
                        FROM `finops360-dev-2025.test.env_daily_costs`
                        WHERE (LOWER(environment) LIKE '%test%' OR LOWER(environment) LIKE '%stage%' OR LOWER(environment) LIKE '%qa%')
                        AND tr_product_pillar_team = t.tr_product_pillar_team
                        AND service_name = t.service_name
                        AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()),
    (SELECT AVG(daily_cost)
     FROM `finops360-dev-2025.test.env_daily_costs`
     WHERE (LOWER(environment) LIKE '%test%' OR LOWER(environment) LIKE '%stage%' OR LOWER(environment) LIKE '%qa%')
     AND tr_product_pillar_team = t.tr_product_pillar_team
     AND service_name = t.service_name
     AND date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE())
  ) * 100 AS projected_growth_pct
FROM
  `finops360-dev-2025.test.test_forecast` t;