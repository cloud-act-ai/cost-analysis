-- Environment Analysis GenAI Summary

-- Step 1: Create a consolidated view for GenAI analysis
CREATE OR REPLACE TABLE `finops360-dev-2025.test.env_analysis_consolidated` AS

-- Environment summary metrics
WITH env_summary AS (
  SELECT
    environment_category,
    SUM(total_cost) AS total_cost,
    AVG(avg_daily_cost) AS avg_daily_cost,
    COUNT(DISTINCT tr_product) AS product_count,
    COUNT(DISTINCT service_name) AS service_count
  FROM
    `finops360-dev-2025.test.env_cost_summary`
  GROUP BY
    environment_category
),

-- Anomaly statistics
anomaly_stats AS (
  SELECT
    environment_category,
    COUNT(*) AS anomaly_count,
    AVG(percent_change) AS avg_anomaly_pct_change,
    COUNT(CASE WHEN severity = 'Critical' THEN 1 END) AS critical_anomalies,
    COUNT(CASE WHEN severity = 'High' THEN 1 END) AS high_anomalies
  FROM
    `finops360-dev-2025.test.env_anomalies_consolidated`
  GROUP BY
    environment_category
),

-- Forecast statistics for end of forecast period (30 days out)
forecast_stats AS (
  SELECT
    environment_category,
    AVG(projected_growth_pct) AS avg_projected_growth_pct,
    SUM(forecasted_cost) AS total_forecasted_cost,
    SUM(current_avg_cost) AS total_current_cost
  FROM
    `finops360-dev-2025.test.env_forecasts_consolidated`
  WHERE
    -- Get the last day in the forecast period (30 days from now)
    DATE(forecast_date) = DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY
    environment_category
),

-- Efficiency metrics
efficiency_overview AS (
  SELECT
    AVG(non_prod_to_prod_ratio) AS avg_non_prod_to_prod_ratio,
    AVG(dev_to_prod_ratio) AS avg_dev_to_prod_ratio,
    AVG(test_to_prod_ratio) AS avg_test_to_prod_ratio,
    COUNT(CASE WHEN efficiency_rating = 'Excellent (< 30%)' THEN 1 END) AS excellent_efficiency_count,
    COUNT(CASE WHEN efficiency_rating = 'Good (30-50%)' THEN 1 END) AS good_efficiency_count,
    COUNT(CASE WHEN efficiency_rating = 'Fair (50-70%)' THEN 1 END) AS fair_efficiency_count,
    COUNT(CASE WHEN efficiency_rating = 'Poor (70-100%)' THEN 1 END) AS poor_efficiency_count,
    COUNT(CASE WHEN efficiency_rating = 'Very Poor (>100%)' THEN 1 END) AS very_poor_efficiency_count
  FROM
    `finops360-dev-2025.test.env_efficiency_metrics`
),

-- Top cost items per environment
top_costs AS (
  SELECT
    environment_category,
    STRING_AGG(CONCAT(tr_product, ' (', service_name, '): $', CAST(ROUND(total_cost, 2) AS STRING)), ', ' ORDER BY total_cost DESC LIMIT 3) AS top_3_cost_items
  FROM
    `finops360-dev-2025.test.env_cost_rankings`
  WHERE
    cost_rank <= 3
  GROUP BY
    environment_category
)

-- Combine all statistics into a single row per environment for GenAI summarization
SELECT
  s.environment_category,
  s.total_cost,
  s.avg_daily_cost,
  s.product_count,
  s.service_count,
  a.anomaly_count,
  a.avg_anomaly_pct_change,
  a.critical_anomalies,
  a.high_anomalies,
  f.avg_projected_growth_pct,
  f.total_forecasted_cost,
  f.total_current_cost,
  CASE 
    WHEN s.environment_category = 'Production' THEN 0.0 -- Production is our baseline
    ELSE e.avg_non_prod_to_prod_ratio
  END AS avg_non_prod_to_prod_ratio,
  t.top_3_cost_items,
  CURRENT_DATE() AS analysis_date,
  -- Generate natural language summary (SQL-based instead of LLM)
  CASE
    WHEN s.environment_category = 'Production' THEN
      CONCAT(
        'Production environment total cost: $', CAST(ROUND(s.total_cost, 2) AS STRING), 
        ' across ', CAST(s.product_count AS STRING), ' products and ', 
        CAST(s.service_count AS STRING), ' services. ',
        'Detected ', CAST(a.anomaly_count AS STRING), ' anomalies ',
        '(', CAST(a.critical_anomalies AS STRING), ' critical). ',
        'Forecast projects ', ROUND(f.avg_projected_growth_pct, 1), '% growth over next 30 days. ',
        'Top cost items: ', t.top_3_cost_items, '.'
      )
    WHEN s.environment_category = 'Development' THEN
      CONCAT(
        'Development environment total cost: $', CAST(ROUND(s.total_cost, 2) AS STRING), 
        ' (', ROUND(s.total_cost / (SELECT total_cost FROM env_summary WHERE environment_category = 'Production') * 100, 1), '% of production). ',
        'Dev-to-Prod ratio: ', ROUND(e.avg_dev_to_prod_ratio, 2), '. ',
        'Detected ', CAST(a.anomaly_count AS STRING), ' anomalies. ',
        'Forecast projects ', ROUND(f.avg_projected_growth_pct, 1), '% growth over next 30 days. ',
        'Top cost items: ', t.top_3_cost_items, '.'
      )
    WHEN s.environment_category = 'Test/Stage' THEN
      CONCAT(
        'Test/Stage environment total cost: $', CAST(ROUND(s.total_cost, 2) AS STRING), 
        ' (', ROUND(s.total_cost / (SELECT total_cost FROM env_summary WHERE environment_category = 'Production') * 100, 1), '% of production). ',
        'Test-to-Prod ratio: ', ROUND(e.avg_test_to_prod_ratio, 2), '. ',
        'Detected ', CAST(a.anomaly_count AS STRING), ' anomalies. ',
        'Forecast projects ', ROUND(f.avg_projected_growth_pct, 1), '% growth over next 30 days. ',
        'Top cost items: ', t.top_3_cost_items, '.'
      )
    ELSE
      'Other environments'
  END AS environment_summary,
  
  -- Generate recommendations based on the analysis (SQL-based rules)
  CASE
    WHEN s.environment_category = 'Production' THEN
      CASE
        WHEN a.critical_anomalies > 0 THEN 'CRITICAL: Investigate production cost spikes immediately, focusing on anomalies with highest percentage change.'
        WHEN f.avg_projected_growth_pct > 15 THEN 'WARNING: Production costs projected to increase significantly. Review capacity planning and optimization opportunities.'
        WHEN f.avg_projected_growth_pct < -15 THEN 'ALERT: Production costs projected to decrease significantly. Verify if this aligns with expected changes or if there could be service disruptions.'
        ELSE 'Production costs appear stable. Continue monitoring and implement regular cost reviews.'
      END
    WHEN s.environment_category = 'Development' THEN
      CASE
        WHEN e.avg_dev_to_prod_ratio > 0.5 THEN 'ACTION NEEDED: Development costs are over 50% of production costs! Implement automated scaling down of dev resources during non-business hours.'
        WHEN a.anomaly_count > 5 THEN 'WARNING: Multiple cost anomalies detected in development. Check for abandoned or oversized development resources.'
        WHEN f.avg_projected_growth_pct > 20 THEN 'ALERT: Development costs growing faster than expected. Review recent project launches and CI/CD pipeline costs.'
        ELSE 'Development environment costs appear reasonable. Continue monitoring dev-to-prod ratio.'
      END
    WHEN s.environment_category = 'Test/Stage' THEN
      CASE
        WHEN e.avg_test_to_prod_ratio > 0.3 THEN 'ACTION NEEDED: Test/Stage costs are over 30% of production costs. Implement ephemeral testing environments that automatically deprovision.'
        WHEN a.anomaly_count > 3 THEN 'WARNING: Multiple cost anomalies detected in test/stage. Check for test environments that weren\'t properly decommissioned.'
        WHEN f.avg_projected_growth_pct > 10 THEN 'ALERT: Test/Stage costs growing. Verify if this aligns with QA testing cycles or indicates resource leakage.'
        ELSE 'Test/Stage environment costs appear reasonable. Continue monitoring the test-to-prod ratio.'
      END
    ELSE 'No recommendations available for this environment category.'
  END AS recommendation
FROM
  env_summary s
LEFT JOIN
  anomaly_stats a ON s.environment_category = a.environment_category
LEFT JOIN
  forecast_stats f ON s.environment_category = f.environment_category
LEFT JOIN
  top_costs t ON s.environment_category = t.environment_category
CROSS JOIN
  efficiency_overview e  -- Efficiency metrics are global, not per environment
WHERE
  s.environment_category IN ('Production', 'Development', 'Test/Stage');