-- Create view for average daily costs using the exact logic provided
-- Set variables (replace with your actual project and dataset)
DECLARE PROJECT_ID STRING DEFAULT 'finops360-dev-2025';
DECLARE DATASET STRING DEFAULT 'test';
DECLARE COST_TABLE STRING DEFAULT 'cost_analysis_new';
DECLARE AVG_TABLE STRING DEFAULT 'avg_daily_cost_table';

-- Create the view using the provided query logic
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.%s` AS
WITH fiscal_year_averages AS (
    SELECT 
        CASE 
            WHEN environment LIKE '%%PROD%%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        cto,
        -- FY24 Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2023-02-01' AND '2024-01-31' THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2023-02-01' AND '2024-01-31' THEN date ELSE NULL END), 0), 2) AS fy24_avg_daily_spend,
        -- FY25 Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2024-02-01' AND '2025-01-31' THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2024-02-01' AND '2025-01-31' THEN date ELSE NULL END), 0), 2) AS fy25_avg_daily_spend,
        -- FY26 YTD Average Daily Spend
        ROUND(SUM(CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN date ELSE NULL END), 0), 2) AS fy26_ytd_avg_daily_spend,
        -- FY26 Forecasted Average Daily Spend (calculated as 15% increase over YTD)
        ROUND(
            (SUM(CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN cost ELSE 0 END) / 
            NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND CURRENT_DATE() - 3 THEN date ELSE NULL END), 0)) * 1.15, 
            2) AS fy26_forecasted_avg_daily_spend,
        -- FY26 Total Average Daily Spend (YTD + Forecasted)
        ROUND(SUM(CASE WHEN date BETWEEN '2025-02-01' AND '2026-01-31' THEN cost ELSE 0 END) / 
              NULLIF(COUNT(DISTINCT CASE WHEN date BETWEEN '2025-02-01' AND '2026-01-31' THEN date ELSE NULL END), 0), 2) AS fy26_avg_daily_spend
    FROM 
        `%s.%s.%s`
    WHERE 
        date BETWEEN '2023-02-01' AND '2026-01-31'
    GROUP BY 
        environment_type, cto
),
daily_costs AS (
    SELECT 
        date,
        CASE 
            WHEN environment LIKE '%%PROD%%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        cto,
        ROUND(SUM(cost), 2) AS daily_cost -- Daily cost for each specific date
    FROM 
        `%s.%s.%s`
    WHERE 
        date BETWEEN '2023-02-01' AND '2026-01-31'
    GROUP BY 
        date, environment_type, cto
)
SELECT 
    d.date,
    d.environment_type,
    d.cto,
    COALESCE(f.fy24_avg_daily_spend, 0) AS fy24_avg_daily_spend,
    COALESCE(f.fy25_avg_daily_spend, 0) AS fy25_avg_daily_spend,
    COALESCE(f.fy26_ytd_avg_daily_spend, 0) AS fy26_ytd_avg_daily_spend,
    COALESCE(f.fy26_forecasted_avg_daily_spend, 0) AS fy26_forecasted_avg_daily_spend,
    COALESCE(f.fy26_avg_daily_spend, 0) AS fy26_avg_daily_spend,
    d.daily_cost
FROM 
    daily_costs d
LEFT JOIN 
    fiscal_year_averages f
ON 
    d.environment_type = f.environment_type
    AND d.cto = f.cto
ORDER BY 
    d.date DESC, d.environment_type, d.cto
""", PROJECT_ID, DATASET, AVG_TABLE, PROJECT_ID, DATASET, COST_TABLE, PROJECT_ID, DATASET, COST_TABLE);

-- Create additional useful views for dashboards

-- 1. Environment cost breakdown view
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.environment_breakdown` AS
SELECT
  date,
  environment_type,
  SUM(daily_cost) AS total_daily_cost,
  SUM(fy24_avg_daily_spend) AS total_fy24_avg_daily_spend,
  SUM(fy25_avg_daily_spend) AS total_fy25_avg_daily_spend,
  SUM(fy26_ytd_avg_daily_spend) AS total_fy26_ytd_avg_daily_spend,
  SUM(fy26_forecasted_avg_daily_spend) AS total_fy26_forecasted_avg_daily_spend,
  SUM(fy26_avg_daily_spend) AS total_fy26_avg_daily_spend,
  (SUM(daily_cost) / SUM(fy25_avg_daily_spend) - 1) * 100 AS yoy_percent_change
FROM
  `%s.%s.%s`
GROUP BY
  date, environment_type
ORDER BY
  date DESC, environment_type
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, AVG_TABLE);

-- 2. CTO cost trends view
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.cto_cost_trends` AS
SELECT
  cto,
  environment_type,
  AVG(fy24_avg_daily_spend) AS avg_fy24_spend,
  AVG(fy25_avg_daily_spend) AS avg_fy25_spend,
  AVG(fy26_ytd_avg_daily_spend) AS avg_fy26_ytd_spend,
  AVG(fy26_forecasted_avg_daily_spend) AS avg_fy26_forecasted_spend,
  (AVG(fy25_avg_daily_spend) / NULLIF(AVG(fy24_avg_daily_spend), 0) - 1) * 100 AS fy24_to_fy25_growth,
  (AVG(fy26_ytd_avg_daily_spend) / NULLIF(AVG(fy25_avg_daily_spend), 0) - 1) * 100 AS fy25_to_fy26_growth,
  (AVG(fy26_forecasted_avg_daily_spend) / NULLIF(AVG(fy26_ytd_avg_daily_spend), 0) - 1) * 100 AS forecasted_growth
FROM
  `%s.%s.%s`
GROUP BY
  cto, environment_type
ORDER BY
  avg_fy26_ytd_spend DESC, cto, environment_type
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, AVG_TABLE);

-- 3. Monthly forecast dashboard view
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.monthly_forecasts` AS
WITH monthly_data AS (
  SELECT
    DATE_TRUNC(date, MONTH) AS month,
    environment_type,
    cto,
    AVG(fy26_ytd_avg_daily_spend) AS monthly_ytd_avg,
    AVG(fy26_forecasted_avg_daily_spend) AS monthly_forecast_avg,
    AVG(daily_cost) AS actual_monthly_avg,
    COUNT(DISTINCT date) AS day_count
  FROM
    `%s.%s.%s`
  GROUP BY
    month, environment_type, cto
)
SELECT
  month,
  environment_type,
  cto,
  monthly_ytd_avg,
  monthly_forecast_avg,
  actual_monthly_avg,
  monthly_ytd_avg * day_count AS monthly_ytd_total,
  monthly_forecast_avg * day_count AS monthly_forecast_total,
  actual_monthly_avg * day_count AS actual_monthly_total,
  (monthly_forecast_avg - monthly_ytd_avg) / NULLIF(monthly_ytd_avg, 0) * 100 AS forecast_percent_change
FROM
  monthly_data
ORDER BY
  month DESC, environment_type, monthly_forecast_total DESC
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, AVG_TABLE);

-- 4. Year-over-year comparison view
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.year_over_year_comparison` AS
SELECT
  date,
  environment_type,
  cto,
  daily_cost AS current_day_cost,
  fy25_avg_daily_spend AS previous_year_avg,
  (daily_cost - fy25_avg_daily_spend) AS absolute_change,
  (daily_cost / NULLIF(fy25_avg_daily_spend, 0) - 1) * 100 AS percent_change,
  CASE
    WHEN daily_cost > fy25_avg_daily_spend * 1.10 THEN 'Significant Increase'
    WHEN daily_cost > fy25_avg_daily_spend * 1.05 THEN 'Moderate Increase'
    WHEN daily_cost < fy25_avg_daily_spend * 0.95 THEN 'Moderate Decrease'
    WHEN daily_cost < fy25_avg_daily_spend * 0.90 THEN 'Significant Decrease'
    ELSE 'Stable'
  END AS change_category
FROM
  `%s.%s.%s`
ORDER BY
  date DESC, percent_change DESC
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, AVG_TABLE);

-- 5. Cost breakdown by detailed categories
EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `%s.%s.detailed_cost_categories` AS
SELECT
  a.date,
  a.environment_type,
  a.cto,
  c.cloud,
  c.tr_product_pillar_team,
  c.tr_product,
  c.managed_service,
  SUM(c.cost) AS detailed_cost,
  a.daily_cost AS total_daily_cost,
  SUM(c.cost) / a.daily_cost * 100 AS percent_of_daily
FROM
  `%s.%s.%s` a
JOIN
  `%s.%s.%s` c
ON
  a.date = c.date
  AND (a.environment_type = 'PROD' AND c.environment LIKE '%%PROD%%'
       OR a.environment_type = 'NON-PROD' AND c.environment NOT LIKE '%%PROD%%')
  AND a.cto = c.cto
GROUP BY
  a.date, a.environment_type, a.cto, c.cloud, c.tr_product_pillar_team, c.tr_product, c.managed_service, a.daily_cost
ORDER BY
  a.date DESC, detailed_cost DESC
""", PROJECT_ID, DATASET, PROJECT_ID, DATASET, AVG_TABLE, PROJECT_ID, DATASET, COST_TABLE);

-- Confirm view creation
SELECT 'All views created successfully' AS status;