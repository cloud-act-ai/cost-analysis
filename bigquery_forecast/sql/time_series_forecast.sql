-- Time Series Forecast for Cost Analysis
-- Using ML.FORECAST built-in function with simplified model

WITH forecast_results AS (
  SELECT
    *
  FROM
    ML.FORECAST(MODEL `finops360-dev-2025.test.ts_forecast_model`,
              STRUCT(30 AS horizon, 0.9 AS confidence_level))
),

-- Add environment and project details back in for reporting
service_details AS (
  SELECT
    service_name,
    environment,
    project_id,
    tr_product_pillar_team,
    tr_product,
    owner,
    MAX(cost) as max_cost -- Just using this to get a row for joining
  FROM
    `finops360-dev-2025.test.cost_analysis_test`
  GROUP BY
    service_name, environment, project_id, tr_product_pillar_team, tr_product, owner
)

-- Final forecast results with additional context
SELECT
  f.forecast_timestamp as forecast_date,
  f.service_name,
  d.environment,
  d.project_id,
  d.tr_product_pillar_team,
  d.tr_product,
  d.owner,
  f.forecast_value as forecasted_cost,
  f.prediction_interval_lower_bound as min_cost,
  f.prediction_interval_upper_bound as max_cost,
  ROUND((f.prediction_interval_upper_bound - f.prediction_interval_lower_bound) / f.forecast_value * 100, 2) as uncertainty_pct
FROM
  forecast_results f
JOIN
  service_details d
ON
  f.service_name = d.service_name
ORDER BY
  f.service_name, f.forecast_timestamp