-- GenAI Cost Analysis using manual analysis (without ML model)
-- Focusing on basic cost summary metrics instead

-- Create cost summary table
CREATE OR REPLACE TABLE `finops360-dev-2025.test.cost_summary` AS
SELECT
  tr_product_pillar_team,
  tr_product,
  service_name,
  environment,
  cto,
  vp,
  owner,
  application,
  project_id,
  SUM(cost) as total_cost,
  MIN(date) as start_date,
  MAX(date) as end_date,
  COUNT(DISTINCT date) as num_days,
  fy,
  Month,
  
  -- Calculate daily averages and other metrics
  ROUND(SUM(cost) / COUNT(DISTINCT date), 2) as avg_daily_cost,
  
  -- Cost distribution metrics
  CASE
    WHEN SUM(cost) > 10000 THEN 'Very High'
    WHEN SUM(cost) > 5000 THEN 'High'
    WHEN SUM(cost) > 1000 THEN 'Medium'
    WHEN SUM(cost) > 100 THEN 'Low'
    ELSE 'Very Low'
  END as cost_tier,
  
  -- Environment-based classification
  CASE 
    WHEN LOWER(environment) LIKE '%prod%' THEN 'Production'
    WHEN LOWER(environment) LIKE '%dev%' THEN 'Development'
    WHEN LOWER(environment) LIKE '%test%' THEN 'Testing'
    WHEN LOWER(environment) LIKE '%stage%' THEN 'Staging'
    ELSE environment
  END as environment_category,
  
  -- Service categorization
  CASE
    WHEN LOWER(service_name) LIKE '%compute%' OR LOWER(service_name) LIKE '%instance%' THEN 'Compute'
    WHEN LOWER(service_name) LIKE '%storage%' OR LOWER(service_name) LIKE '%bucket%' THEN 'Storage'
    WHEN LOWER(service_name) LIKE '%database%' OR LOWER(service_name) LIKE '%sql%' THEN 'Database'
    WHEN LOWER(service_name) LIKE '%network%' OR LOWER(service_name) LIKE '%lb%' THEN 'Networking'
    ELSE 'Other'
  END as service_category
FROM
  `finops360-dev-2025.test.cost_analysis_test`
WHERE
  date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND CURRENT_DATE()
GROUP BY
  tr_product_pillar_team, tr_product, service_name, environment, cto, vp, owner, 
  application, project_id, fy, Month
ORDER BY
  total_cost DESC;

-- Query to show key insights without ML model
SELECT
  tr_product_pillar_team,
  tr_product,
  service_name,
  environment,
  owner,
  application,
  project_id,
  total_cost,
  avg_daily_cost,
  start_date,
  end_date,
  cost_tier,
  environment_category,
  service_category,
  -- Generate optimization suggestion based on basic rules
  CASE
    WHEN environment_category = 'Development' AND cost_tier IN ('High', 'Very High') 
      THEN 'Consider implementing dev environment auto-shutdown policies'
    WHEN service_category = 'Compute' AND cost_tier IN ('High', 'Very High')
      THEN 'Review compute resource utilization and consider rightsizing'
    WHEN service_category = 'Storage' AND cost_tier IN ('High', 'Very High')
      THEN 'Implement lifecycle policies to archive or delete old data'
    WHEN service_category = 'Database' AND cost_tier IN ('High', 'Very High')
      THEN 'Review database resource allocation and query performance'
    ELSE 'Monitor cost trends and implement tagging for better allocation visibility'
  END as optimization_suggestion
FROM
  `finops360-dev-2025.test.cost_summary`
WHERE
  total_cost > 100
ORDER BY
  total_cost DESC
LIMIT 10