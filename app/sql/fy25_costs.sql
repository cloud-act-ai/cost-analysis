-- Basic FY25 costs query
SELECT
    CASE 
        WHEN environment LIKE 'PROD%' THEN 'PROD'
        WHEN environment LIKE '%NON-PROD%' THEN 'NON-PROD'
        ELSE 'OTHER'
    END AS environment_type,
    SUM(cost) AS total_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2024-02-01' AND '2025-01-31'
GROUP BY environment_type