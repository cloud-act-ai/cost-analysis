-- Product costs query grouped by pillar team and product ID
SELECT
    tr_product_pillar_team || ' - ' || tr_product_id AS display_id,
    tr_product AS product_name,
    tr_product_pillar_team AS pillar_team,
    tr_product_id AS product_id,
    cto AS cto_org,
    SUM(CASE WHEN environment = 'PROD' THEN cost ELSE 0 END) AS prod_ytd_cost,
    SUM(CASE WHEN environment = 'NON-PROD' THEN cost ELSE 0 END) AS nonprod_ytd_cost,
    SUM(cost) AS total_ytd_cost,
    -- Calculate forecasted cost based on YTD trend (extrapolate to full year)
    SUM(cost) * 365 / NULLIF(DATETIME_DIFF(DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), '2025-02-01', DAY), 0) AS forecasted_cost
FROM `{project_id}.{dataset}.{table}`
WHERE 
    date BETWEEN '2025-02-01' AND DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
    {cto_filter}
    {pillar_filter}
    {product_filter}
GROUP BY display_id, product_name, pillar_team, product_id, cto_org
ORDER BY prod_ytd_cost DESC
LIMIT {top_n}