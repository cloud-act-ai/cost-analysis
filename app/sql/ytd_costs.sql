-- Basic YTD costs query
SELECT
    CASE 
        WHEN environment LIKE 'PROD%' THEN 'PROD'
        WHEN environment LIKE '%NON-PROD%' THEN 'NON-PROD'
        ELSE 'OTHER'
    END AS environment_type,
    SUM(cost) AS ytd_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2025-02-01' AND DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
GROUP BY environment_type