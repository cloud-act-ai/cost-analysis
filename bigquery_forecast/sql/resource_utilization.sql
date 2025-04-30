-- Resource Utilization Analysis
-- Identifies resources with high cost but potential low utilization

WITH resource_costs AS (
  SELECT
    tr_product,
    service_name,
    environment,
    project_id,
    cto,
    vp,
    owner,
    application,
    region,
    SUM(cost) AS total_cost,
    COUNT(DISTINCT date) AS active_days
  FROM
    `finops360-dev-2025.test.cost_analysis_test`
  WHERE
    date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND CURRENT_DATE()
  GROUP BY
    tr_product, service_name, environment, project_id, cto, vp, owner, application, region
),

utilization_metrics AS (
  SELECT
    *,
    CASE
      -- Compute resources with high costs but used less than 50% of days
      WHEN REGEXP_CONTAINS(service_name, r'Compute|VM|Instance') AND active_days < 15 THEN 'Low'
      -- Storage resources with steady costs (expected)
      WHEN REGEXP_CONTAINS(service_name, r'Storage|Disk|Bucket') THEN 'Expected'
      -- Other resources used less than 20% of days
      WHEN active_days < 6 THEN 'Very Low'
      -- Resources used more than 20% but less than 70% of days
      WHEN active_days < 21 THEN 'Medium'
      -- Resources used more than 70% of days
      ELSE 'High'
    END AS utilization_level,
    
    -- Calculate cost per active day
    SAFE_DIVIDE(total_cost, active_days) AS cost_per_active_day
  FROM
    resource_costs
)

SELECT
  tr_product,
  service_name,
  environment,
  project_id,
  cto,
  vp,
  owner,
  application,
  region,
  total_cost,
  active_days,
  ROUND(cost_per_active_day, 2) AS cost_per_active_day,
  utilization_level,
  CASE
    WHEN utilization_level IN ('Low', 'Very Low') AND total_cost > 100 THEN TRUE
    ELSE FALSE
  END AS optimization_candidate
FROM
  utilization_metrics
ORDER BY
  CASE
    WHEN utilization_level = 'Very Low' THEN 1
    WHEN utilization_level = 'Low' THEN 2
    WHEN utilization_level = 'Medium' THEN 3
    WHEN utilization_level = 'High' THEN 4
    ELSE 5
  END,
  total_cost DESC