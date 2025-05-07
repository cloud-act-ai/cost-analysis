-- SQL script for creating views on the cost analysis tables
-- These views can be used for standard reporting scenarios

-- Set variables (replace with your actual project and dataset)
DECLARE PROJECT_ID STRING DEFAULT 'finops360-dev-2025';
DECLARE DATASET STRING DEFAULT 'test';
DECLARE COST_TABLE STRING DEFAULT 'cost_analysis_new';
DECLARE AVG_TABLE STRING DEFAULT 'avg_daily_cost_table';

-- 1. Daily cost by environment and cloud view
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.daily_cost_by_env_cloud` AS
SELECT
  date,
  environment,
  cloud,
  SUM(cost) AS total_cost
FROM
  `%s.%s.%s`
GROUP BY
  date,
  environment,
  cloud
ORDER BY
  date DESC,
  environment,
  cloud
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, COST_TABLE);

-- 2. Monthly cost by CTO view
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.monthly_cost_by_cto` AS
SELECT
  EXTRACT(YEAR FROM date) AS year,
  EXTRACT(MONTH FROM date) AS month,
  cto,
  SUM(cost) AS total_cost
FROM
  `%s.%s.%s`
GROUP BY
  year,
  month,
  cto
ORDER BY
  year DESC,
  month DESC,
  total_cost DESC
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, COST_TABLE);

-- 3. Product pillar team cost trends
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.product_team_cost_trends` AS
SELECT
  date,
  tr_product_pillar_team,
  environment,
  SUM(cost) AS total_cost
FROM
  `%s.%s.%s`
GROUP BY
  date,
  tr_product_pillar_team,
  environment
ORDER BY
  date DESC,
  total_cost DESC
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, COST_TABLE);

-- 4. Fiscal year comparison view combining both tables
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.fiscal_year_comparison` AS
SELECT
  a.date,
  a.environment_type AS environment,
  a.cto,
  a.fy24_avg_daily_spend,
  a.fy25_avg_daily_spend,
  a.fy26_avg_daily_spend,
  b.total_cost AS current_cost
FROM
  `%s.%s.%s` a
LEFT JOIN (
  SELECT
    DATE_TRUNC(date, MONTH) AS month_date,
    environment AS env,
    cto,
    SUM(cost) AS total_cost
  FROM
    `%s.%s.%s`
  GROUP BY
    month_date,
    env,
    cto
) b
ON DATE_TRUNC(a.date, MONTH) = b.month_date
   AND LOWER(a.environment_type) = LOWER(b.env)
   AND a.cto = b.cto
ORDER BY
  a.date DESC,
  a.environment_type,
  a.cto
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, AVG_TABLE, PROJECT_ID, DATASET, COST_TABLE);

-- 5. Cost forecast view
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.cost_forecast` AS
SELECT
  a.date,
  a.environment_type AS environment,
  a.cto,
  a.fy26_ytd_avg_daily_spend AS current_spend,
  a.fy26_forecasted_avg_daily_spend AS forecasted_spend,
  a.fy26_avg_daily_spend AS total_spend,
  a.fy26_forecasted_avg_daily_spend / NULLIF(a.fy26_ytd_avg_daily_spend, 0) * 100 - 100 AS percent_change
FROM
  `%s.%s.%s` a
WHERE
  a.fy26_forecasted_avg_daily_spend > 0
ORDER BY
  a.date DESC,
  a.environment_type,
  percent_change DESC
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, AVG_TABLE);

-- 6. Top managed services by cost
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.top_managed_services` AS
SELECT
  managed_service,
  cloud,
  environment,
  SUM(cost) AS total_cost,
  COUNT(DISTINCT date) AS days_count,
  SUM(cost) / COUNT(DISTINCT date) AS avg_daily_cost
FROM
  `%s.%s.%s`
GROUP BY
  managed_service,
  cloud,
  environment
ORDER BY
  total_cost DESC
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, COST_TABLE);

-- Print success message
SELECT 'All views created successfully' AS status;