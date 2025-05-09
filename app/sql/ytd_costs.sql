-- Basic YTD costs query
SELECT
    CASE 
        WHEN environment = 'PROD' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    SUM(cost) AS ytd_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2025-02-01' AND DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
GROUP BY environment_type