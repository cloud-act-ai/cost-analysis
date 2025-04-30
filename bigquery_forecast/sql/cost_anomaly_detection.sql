-- Cost Anomaly Detection using Z-Score method
WITH daily_costs AS (
  SELECT 
    date,
    service_name,
    environment,
    tr_product_pillar_team,
    tr_product,
    application,
    project_id,
    SUM(cost) as daily_cost
  FROM 
    `finops360-dev-2025.test.cost_analysis_test`
  WHERE 
    date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND CURRENT_DATE()
  GROUP BY 
    date, service_name, environment, tr_product_pillar_team, tr_product, application, project_id
),

service_stats AS (
  SELECT
    service_name,
    environment,
    project_id,
    tr_product,
    AVG(daily_cost) as avg_cost,
    STDDEV(daily_cost) as stddev_cost
  FROM
    daily_costs
  GROUP BY
    service_name, environment, project_id, tr_product
)

SELECT
  d.date,
  d.service_name,
  d.environment,
  d.tr_product_pillar_team,
  d.tr_product,
  d.application,
  d.project_id,
  d.daily_cost,
  s.avg_cost,
  s.stddev_cost,
  (d.daily_cost - s.avg_cost) / NULLIF(s.stddev_cost, 0) as z_score,
  CASE
    WHEN ABS((d.daily_cost - s.avg_cost) / NULLIF(s.stddev_cost, 0)) > 2.5 THEN TRUE
    ELSE FALSE
  END as is_anomaly
FROM
  daily_costs d
JOIN
  service_stats s
ON
  d.service_name = s.service_name
  AND d.environment = s.environment
  AND d.project_id = s.project_id
  AND d.tr_product = s.tr_product
WHERE
  s.stddev_cost > 0  -- Only consider services with some cost variation
ORDER BY
  ABS((d.daily_cost - s.avg_cost) / NULLIF(s.stddev_cost, 0)) DESC