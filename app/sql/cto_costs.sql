-- CTO costs query grouped by CTO organization
SELECT
    cto AS cto_org,
    SUM(CASE WHEN environment = 'PROD' THEN cost ELSE 0 END) AS prod_ytd_cost,
    SUM(CASE WHEN environment = 'NON-PROD' THEN cost ELSE 0 END) AS nonprod_ytd_cost,
    SUM(cost) AS total_ytd_cost,
    SUM(CASE WHEN environment = 'NON-PROD' THEN cost ELSE 0 END) / NULLIF(SUM(cost), 0) * 100 AS nonprod_percentage
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2025-02-01' AND DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
GROUP BY cto_org
ORDER BY total_ytd_cost DESC
LIMIT {top_n}