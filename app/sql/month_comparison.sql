-- Basic month-to-month comparison query
SELECT
    CASE 
        WHEN environment = 'PROD' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    SUM(CASE WHEN date BETWEEN '{this_month_start}' AND '{this_month_end}' THEN cost ELSE 0 END) AS this_month_cost,
    SUM(CASE WHEN date BETWEEN '{prev_month_start}' AND '{prev_month_end}' THEN cost ELSE 0 END) AS prev_month_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '{prev_month_start}' AND '{this_month_end}'
    {cto_filter}
    {pillar_filter}
    {product_filter}
GROUP BY environment_type