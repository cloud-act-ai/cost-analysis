-- Pills (pillars) costs query grouped by product pillar team
SELECT
    tr_product_pillar_team AS pillar_name,
    COUNT(DISTINCT tr_product_id) AS product_count,
    SUM(CASE WHEN environment LIKE 'PROD%' THEN cost ELSE 0 END) AS prod_ytd_cost,
    SUM(CASE WHEN environment LIKE '%NON-PROD%' THEN cost ELSE 0 END) AS nonprod_ytd_cost,
    SUM(cost) AS total_ytd_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2025-02-01' AND DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
GROUP BY pillar_name
HAVING SUM(CASE WHEN environment LIKE '%NON-PROD%' THEN cost ELSE 0 END) > 0
ORDER BY nonprod_ytd_cost DESC
LIMIT {top_n}