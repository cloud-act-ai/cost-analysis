-- Environment Anomaly Detection using BigQuery ML.DETECT_ANOMALIES
-- Detects anomalies across different environments

-- Step 1: Create environment cost time series
CREATE OR REPLACE TABLE `finops360-dev-2025.test.env_daily_costs` AS
SELECT
  date,
  environment,
  tr_product_pillar_team,
  tr_product,
  service_name,
  SUM(cost) AS daily_cost
FROM
  `finops360-dev-2025.test.cost_analysis_test`
WHERE
  date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY) AND CURRENT_DATE()
GROUP BY
  date, environment, tr_product_pillar_team, tr_product, service_name;

-- Step 2: Production Environment Anomalies
CREATE OR REPLACE TABLE `finops360-dev-2025.test.prod_anomalies` AS
WITH prod_data AS (
  SELECT
    *
  FROM
    `finops360-dev-2025.test.env_daily_costs`
  WHERE
    LOWER(environment) LIKE '%prod%'
)
SELECT
  *
FROM
  ML.DETECT_ANOMALIES(
    MODEL `finops360-dev-2025.test.env_prod_model`,
    STRUCT(0.95 AS anomaly_prob_threshold)
  );

-- Step 3: Development Environment Anomalies
CREATE OR REPLACE TABLE `finops360-dev-2025.test.dev_anomalies` AS
WITH dev_data AS (
  SELECT
    *
  FROM
    `finops360-dev-2025.test.env_daily_costs`
  WHERE
    LOWER(environment) LIKE '%dev%'
)
SELECT
  *
FROM
  ML.DETECT_ANOMALIES(
    MODEL `finops360-dev-2025.test.env_dev_model`,
    STRUCT(0.95 AS anomaly_prob_threshold)
  );

-- Step 4: Test/Stage Environment Anomalies
CREATE OR REPLACE TABLE `finops360-dev-2025.test.test_anomalies` AS
WITH test_data AS (
  SELECT
    *
  FROM
    `finops360-dev-2025.test.env_daily_costs`
  WHERE
    LOWER(environment) LIKE '%test%' OR LOWER(environment) LIKE '%stage%' OR LOWER(environment) LIKE '%qa%'
)
SELECT
  *
FROM
  ML.DETECT_ANOMALIES(
    MODEL `finops360-dev-2025.test.env_test_model`,
    STRUCT(0.95 AS anomaly_prob_threshold)
  );

-- Step 5: Consolidated anomalies view with severity classification
CREATE OR REPLACE TABLE `finops360-dev-2025.test.env_anomalies_consolidated` AS
WITH all_anomalies AS (
  SELECT 
    date, 
    'Production' AS environment_category,
    tr_product_pillar_team,
    service_name,
    total_cost AS cost,
    anomaly_probability,
    is_anomaly
  FROM 
    `finops360-dev-2025.test.prod_anomalies`
  WHERE 
    is_anomaly = TRUE
  
  UNION ALL
  
  SELECT 
    date, 
    'Development' AS environment_category,
    tr_product_pillar_team,
    service_name,
    total_cost AS cost,
    anomaly_probability,
    is_anomaly
  FROM 
    `finops360-dev-2025.test.dev_anomalies`
  WHERE 
    is_anomaly = TRUE
  
  UNION ALL
  
  SELECT 
    date, 
    'Test/Stage' AS environment_category,
    tr_product_pillar_team,
    service_name,
    total_cost AS cost,
    anomaly_probability,
    is_anomaly
  FROM 
    `finops360-dev-2025.test.test_anomalies`
  WHERE 
    is_anomaly = TRUE
)

SELECT
  a.*,
  -- Calculate severity based on anomaly probability
  CASE
    WHEN anomaly_probability > 0.99 THEN 'Critical'
    WHEN anomaly_probability > 0.95 THEN 'High'
    ELSE 'Medium'
  END AS severity,
  
  -- Get baseline cost for comparison
  (SELECT AVG(daily_cost) 
   FROM `finops360-dev-2025.test.env_daily_costs` base
   WHERE 
     base.tr_product_pillar_team = a.tr_product_pillar_team AND
     base.service_name = a.service_name AND
     (
       (a.environment_category = 'Production' AND LOWER(base.environment) LIKE '%prod%') OR
       (a.environment_category = 'Development' AND LOWER(base.environment) LIKE '%dev%') OR
       (a.environment_category = 'Test/Stage' AND (LOWER(base.environment) LIKE '%test%' OR LOWER(base.environment) LIKE '%stage%' OR LOWER(base.environment) LIKE '%qa%'))
     )
   ) AS baseline_cost,
   
  -- Calculate percentage difference from baseline
  SAFE_DIVIDE(
    (cost - (SELECT AVG(daily_cost) 
             FROM `finops360-dev-2025.test.env_daily_costs` base
             WHERE 
               base.tr_product_pillar_team = a.tr_product_pillar_team AND
               base.service_name = a.service_name AND
               (
                 (a.environment_category = 'Production' AND LOWER(base.environment) LIKE '%prod%') OR
                 (a.environment_category = 'Development' AND LOWER(base.environment) LIKE '%dev%') OR
                 (a.environment_category = 'Test/Stage' AND (LOWER(base.environment) LIKE '%test%' OR LOWER(base.environment) LIKE '%stage%' OR LOWER(base.environment) LIKE '%qa%'))
               )
            )),
    (SELECT AVG(daily_cost) 
     FROM `finops360-dev-2025.test.env_daily_costs` base
     WHERE 
       base.tr_product_pillar_team = a.tr_product_pillar_team AND
       base.service_name = a.service_name AND
       (
         (a.environment_category = 'Production' AND LOWER(base.environment) LIKE '%prod%') OR
         (a.environment_category = 'Development' AND LOWER(base.environment) LIKE '%dev%') OR
         (a.environment_category = 'Test/Stage' AND (LOWER(base.environment) LIKE '%test%' OR LOWER(base.environment) LIKE '%stage%' OR LOWER(base.environment) LIKE '%qa%'))
       )
    )
  ) * 100 AS percent_change
FROM 
  all_anomalies a
ORDER BY
  anomaly_probability DESC;