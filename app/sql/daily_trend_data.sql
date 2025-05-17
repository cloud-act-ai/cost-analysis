-- Basic daily trend data query
SELECT
    date,
    CASE
        WHEN environment_type LIKE 'PROD%' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    daily_cost
FROM `{project_id}.{dataset}.{avg_table}`
WHERE date BETWEEN 
    -- Safe fallback to fiscal year start if not specified
    '2025-02-01' AND 
    -- Safe fallback to current date minus 3 days if not specified
    DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
    {cto_filter}
    {pillar_filter}
    {product_filter}
ORDER BY date, environment_type