-- Trend Analysis for Cost Data
-- Analyzes MoM and YoY cost trends

WITH monthly_costs AS (
  SELECT
    EXTRACT(YEAR FROM date) AS year,
    Month,
    tr_product_pillar_team,
    tr_product,
    service_name,
    environment,
    cto,
    vp,
    project_id,
    SUM(cost) AS monthly_cost
  FROM
    `finops360-dev-2025.test.cost_analysis_test`
  WHERE
    date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 13 MONTH) AND CURRENT_DATE()
  GROUP BY
    year, Month, tr_product_pillar_team, tr_product, service_name, environment, cto, vp, project_id
),

current_month AS (
  SELECT
    *,
    CONCAT(CAST(year AS STRING), '-', Month) AS year_month
  FROM
    monthly_costs
  WHERE
    year = EXTRACT(YEAR FROM CURRENT_DATE()) AND
    Month = FORMAT_DATE('%b', CURRENT_DATE())
),

previous_month AS (
  SELECT
    *,
    CONCAT(CAST(year AS STRING), '-', Month) AS year_month
  FROM
    monthly_costs
  WHERE
    (year = EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)) AND
     Month = FORMAT_DATE('%b', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)))
),

previous_year_month AS (
  SELECT
    *,
    CONCAT(CAST(year AS STRING), '-', Month) AS year_month
  FROM
    monthly_costs
  WHERE
    year = EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)) AND
    Month = FORMAT_DATE('%b', CURRENT_DATE())
)

SELECT
  c.year_month AS current_period,
  c.tr_product_pillar_team,
  c.tr_product,
  c.service_name,
  c.environment,
  c.project_id,
  c.cto,
  c.vp,
  c.monthly_cost AS current_cost,
  pm.monthly_cost AS previous_month_cost,
  pym.monthly_cost AS previous_year_cost,
  
  -- Month over Month change
  c.monthly_cost - pm.monthly_cost AS mom_change,
  SAFE_DIVIDE(c.monthly_cost - pm.monthly_cost, pm.monthly_cost) * 100 AS mom_change_percent,
  
  -- Year over Year change
  c.monthly_cost - pym.monthly_cost AS yoy_change,
  SAFE_DIVIDE(c.monthly_cost - pym.monthly_cost, pym.monthly_cost) * 100 AS yoy_change_percent
FROM
  current_month c
LEFT JOIN
  previous_month pm
ON
  c.tr_product = pm.tr_product AND
  c.service_name = pm.service_name AND
  c.environment = pm.environment AND
  c.project_id = pm.project_id
LEFT JOIN
  previous_year_month pym
ON
  c.tr_product = pym.tr_product AND
  c.service_name = pym.service_name AND
  c.environment = pym.environment AND
  c.project_id = pym.project_id
ORDER BY
  ABS(SAFE_DIVIDE(c.monthly_cost - pm.monthly_cost, pm.monthly_cost)) DESC