-- Environment Cost Analysis
-- Creates a comprehensive analysis of environment costs

-- Step 1: Create environment cost summary
CREATE OR REPLACE TABLE `finops360-dev-2025.test.env_cost_summary` AS
SELECT
  environment,
  CASE
    WHEN LOWER(environment) LIKE '%prod%' THEN 'Production'
    WHEN LOWER(environment) LIKE '%dev%' THEN 'Development'
    WHEN LOWER(environment) LIKE '%test%' OR LOWER(environment) LIKE '%stage%' OR LOWER(environment) LIKE '%qa%' THEN 'Test/Stage'
    ELSE 'Other'
  END AS environment_category,
  tr_product_pillar_team,
  tr_product,
  service_name,
  cto,
  vp,
  fy,
  Month,
  COUNT(DISTINCT date) AS days_active,
  SUM(cost) AS total_cost,
  AVG(cost) AS avg_daily_cost,
  MAX(cost) AS max_daily_cost,
  MIN(cost) AS min_daily_cost,
  STDDEV(cost) AS cost_stddev,
  SUM(cost) / NULLIF(COUNT(DISTINCT project_id), 0) AS avg_cost_per_project,
  COUNT(DISTINCT project_id) AS project_count
FROM
  `finops360-dev-2025.test.cost_analysis_test`
WHERE
  date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND CURRENT_DATE()
GROUP BY
  environment, environment_category, tr_product_pillar_team, tr_product, 
  service_name, cto, vp, fy, Month;

-- Step 2: Create environment cost rankings
CREATE OR REPLACE TABLE `finops360-dev-2025.test.env_cost_rankings` AS
WITH env_ranks AS (
  SELECT
    environment_category,
    tr_product_pillar_team,
    tr_product,
    service_name,
    total_cost,
    avg_daily_cost,
    ROW_NUMBER() OVER (PARTITION BY environment_category ORDER BY total_cost DESC) AS cost_rank
  FROM
    `finops360-dev-2025.test.env_cost_summary`
)

SELECT
  *,
  CASE
    WHEN cost_rank <= 5 THEN 'Top 5 Spender'
    WHEN cost_rank <= 10 THEN 'Top 10 Spender'
    WHEN cost_rank <= 20 THEN 'Top 20 Spender'
    ELSE 'Other'
  END AS spending_tier
FROM
  env_ranks
WHERE
  cost_rank <= 50
ORDER BY
  environment_category, cost_rank;

-- Step 3: Environment cost efficiency metrics
CREATE OR REPLACE TABLE `finops360-dev-2025.test.env_efficiency_metrics` AS
WITH prod_costs AS (
  SELECT
    tr_product_pillar_team,
    tr_product,
    service_name,
    SUM(total_cost) AS prod_cost
  FROM
    `finops360-dev-2025.test.env_cost_summary`
  WHERE
    environment_category = 'Production'
  GROUP BY
    tr_product_pillar_team, tr_product, service_name
),

non_prod_costs AS (
  SELECT
    tr_product_pillar_team,
    tr_product,
    service_name,
    SUM(CASE WHEN environment_category = 'Development' THEN total_cost ELSE 0 END) AS dev_cost,
    SUM(CASE WHEN environment_category = 'Test/Stage' THEN total_cost ELSE 0 END) AS test_cost,
    SUM(CASE WHEN environment_category IN ('Development', 'Test/Stage') THEN total_cost ELSE 0 END) AS total_non_prod_cost
  FROM
    `finops360-dev-2025.test.env_cost_summary`
  GROUP BY
    tr_product_pillar_team, tr_product, service_name
)

SELECT
  p.tr_product_pillar_team,
  p.tr_product,
  p.service_name,
  p.prod_cost,
  np.dev_cost,
  np.test_cost,
  np.total_non_prod_cost,
  p.prod_cost + np.total_non_prod_cost AS total_all_env_cost,
  
  -- Calculate efficiency ratios
  SAFE_DIVIDE(np.total_non_prod_cost, p.prod_cost) AS non_prod_to_prod_ratio,
  SAFE_DIVIDE(np.dev_cost, p.prod_cost) AS dev_to_prod_ratio,
  SAFE_DIVIDE(np.test_cost, p.prod_cost) AS test_to_prod_ratio,
  
  -- Calculate cost percentages
  SAFE_DIVIDE(p.prod_cost, p.prod_cost + np.total_non_prod_cost) * 100 AS prod_cost_pct,
  SAFE_DIVIDE(np.dev_cost, p.prod_cost + np.total_non_prod_cost) * 100 AS dev_cost_pct,
  SAFE_DIVIDE(np.test_cost, p.prod_cost + np.total_non_prod_cost) * 100 AS test_cost_pct,
  
  -- Calculate efficiency score (lower is better)
  CASE
    WHEN SAFE_DIVIDE(np.total_non_prod_cost, p.prod_cost) <= 0.3 THEN 'Excellent (< 30%)'
    WHEN SAFE_DIVIDE(np.total_non_prod_cost, p.prod_cost) <= 0.5 THEN 'Good (30-50%)'
    WHEN SAFE_DIVIDE(np.total_non_prod_cost, p.prod_cost) <= 0.7 THEN 'Fair (50-70%)'
    WHEN SAFE_DIVIDE(np.total_non_prod_cost, p.prod_cost) <= 1.0 THEN 'Poor (70-100%)'
    ELSE 'Very Poor (>100%)'
  END AS efficiency_rating
FROM
  prod_costs p
JOIN
  non_prod_costs np
ON
  p.tr_product_pillar_team = np.tr_product_pillar_team
  AND p.tr_product = np.tr_product
  AND p.service_name = np.service_name
WHERE
  p.prod_cost > 0
ORDER BY
  non_prod_to_prod_ratio DESC;