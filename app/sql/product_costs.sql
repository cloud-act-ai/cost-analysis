-- Product costs query grouped by pillar team and product ID
SELECT
    tr_product_pillar_team || ' - ' || tr_product_id AS display_id,
    tr_product AS product_name,
    tr_product_pillar_team AS pillar_team,
    SUM(CASE WHEN environment = 'PROD' THEN cost ELSE 0 END) AS prod_ytd_cost,
    SUM(CASE WHEN environment = 'NON-PROD' THEN cost ELSE 0 END) AS nonprod_ytd_cost,
    SUM(cost) AS total_ytd_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '2025-02-01' AND DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
GROUP BY display_id, product_name, pillar_team
ORDER BY prod_ytd_cost DESC
LIMIT {top_n}