SELECT
    CASE 
        WHEN environment LIKE '%PROD%' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    SUM(cost) AS total_cost,
    COUNT(DISTINCT date) AS days
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2025-02-01' AND '2026-01-31'
GROUP BY environment_type