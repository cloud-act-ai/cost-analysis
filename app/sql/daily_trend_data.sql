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
    IF('{start_date}' = '', '2025-02-01', '{start_date}') AND 
    IF('{end_date}' = '', DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), '{end_date}')
    {cto_filter}
    {pillar_filter}
    {product_filter}
ORDER BY date, environment_type