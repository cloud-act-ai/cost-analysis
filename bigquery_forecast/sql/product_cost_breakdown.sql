-- Product Cost Breakdown Analysis
-- Breaks down costs by product hierarchy

WITH product_hierarchy AS (
  SELECT
    date,
    cto,
    vp,
    tr_product_pillar_team,
    tr_subpillar_id,
    tr_subpillar_name,
    tr_product_id,
    tr_product,
    environment,
    service_name,
    cost,
    fy,
    Month
  FROM
    `finops360-dev-2025.test.cost_analysis_test`
  WHERE
    date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND CURRENT_DATE()
),

aggregate_costs AS (
  SELECT
    cto,
    vp,
    tr_product_pillar_team,
    tr_subpillar_name,
    tr_product,
    environment,
    service_name,
    fy,
    Month,
    SUM(cost) AS total_cost,
    COUNT(DISTINCT date) AS num_days
  FROM
    product_hierarchy
  GROUP BY
    cto, vp, tr_product_pillar_team, tr_subpillar_name, tr_product, 
    environment, service_name, fy, Month
),

-- Calculate percentage contribution at each level
cto_totals AS (
  SELECT
    cto,
    SUM(total_cost) AS cto_cost
  FROM
    aggregate_costs
  GROUP BY
    cto
),

vp_totals AS (
  SELECT
    cto,
    vp,
    SUM(total_cost) AS vp_cost
  FROM
    aggregate_costs
  GROUP BY
    cto, vp
),

pillar_totals AS (
  SELECT
    cto,
    vp,
    tr_product_pillar_team,
    SUM(total_cost) AS pillar_cost
  FROM
    aggregate_costs
  GROUP BY
    cto, vp, tr_product_pillar_team
)

SELECT
  a.cto,
  a.vp,
  a.tr_product_pillar_team,
  a.tr_subpillar_name,
  a.tr_product,
  a.environment,
  a.service_name,
  a.fy,
  a.Month,
  a.total_cost,
  
  -- Percentage contribution to parent levels
  ROUND(SAFE_DIVIDE(a.total_cost, c.cto_cost) * 100, 2) AS pct_of_cto,
  ROUND(SAFE_DIVIDE(a.total_cost, v.vp_cost) * 100, 2) AS pct_of_vp,
  ROUND(SAFE_DIVIDE(a.total_cost, p.pillar_cost) * 100, 2) AS pct_of_pillar,
  
  -- Calculate cost per day
  ROUND(SAFE_DIVIDE(a.total_cost, a.num_days), 2) AS cost_per_day
FROM
  aggregate_costs a
JOIN
  cto_totals c ON a.cto = c.cto
JOIN
  vp_totals v ON a.cto = v.cto AND a.vp = v.vp
JOIN
  pillar_totals p ON a.cto = p.cto AND a.vp = p.vp AND a.tr_product_pillar_team = p.tr_product_pillar_team
ORDER BY
  a.cto, a.vp, a.tr_product_pillar_team, a.total_cost DESC