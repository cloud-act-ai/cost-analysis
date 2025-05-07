WITH product_costs AS (
    SELECT
        tr_product_id AS product_id,
        tr_product AS product_name,
        tr_product_pillar_team AS pillar_team,
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment,
        SUM(cost) AS ytd_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '2025-02-01' AND DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
    GROUP BY product_id, product_name, pillar_team, environment
),
prod_costs AS (
    SELECT
        product_id,
        product_name,
        pillar_team,
        ytd_cost AS prod_ytd_cost
    FROM product_costs
    WHERE environment = 'PROD'
),
nonprod_costs AS (
    SELECT
        product_id,
        product_name,
        pillar_team,
        ytd_cost AS nonprod_ytd_cost
    FROM product_costs
    WHERE environment = 'NON-PROD'
),
combined_costs AS (
    SELECT
        COALESCE(p.product_id, np.product_id) AS product_id,
        COALESCE(p.product_name, np.product_name) AS product_name,
        COALESCE(p.pillar_team, np.pillar_team) AS pillar_team,
        COALESCE(p.prod_ytd_cost, 0) AS prod_ytd_cost,
        COALESCE(np.nonprod_ytd_cost, 0) AS nonprod_ytd_cost,
        COALESCE(p.prod_ytd_cost, 0) + COALESCE(np.nonprod_ytd_cost, 0) AS total_ytd_cost
    FROM prod_costs p
    FULL OUTER JOIN nonprod_costs np ON p.product_id = np.product_id
)
SELECT
    product_id,
    product_name,
    pillar_team,
    prod_ytd_cost,
    nonprod_ytd_cost,
    total_ytd_cost,
    CASE 
        WHEN total_ytd_cost > 0 THEN (nonprod_ytd_cost / total_ytd_cost) * 100
        ELSE 0
    END AS nonprod_percentage
FROM combined_costs
WHERE total_ytd_cost > 0
ORDER BY nonprod_percentage DESC, nonprod_ytd_cost DESC, total_ytd_cost DESC
LIMIT {top_n}