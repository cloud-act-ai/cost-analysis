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