-- Enhanced FY25 costs query that includes YTD values for direct comparison
-- Gets both total FY25 costs and YTD costs for the same period last year
SELECT
    CASE 
        WHEN environment = 'PROD' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    SUM(cost) AS total_cost,
    -- YTD cost for direct comparison with this year's YTD
    SUM(CASE 
        WHEN date BETWEEN '2024-02-01' AND CURRENT_DATE() - INTERVAL 1 YEAR
        THEN cost
        ELSE 0
    END) AS ytd_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2024-02-01' AND '2025-01-31'
    {cto_filter}
    {pillar_filter}
    {product_filter}
GROUP BY environment_type