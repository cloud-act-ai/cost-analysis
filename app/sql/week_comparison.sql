-- Basic week-to-week comparison query
SELECT
    CASE 
        WHEN environment = 'PROD' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    SUM(CASE WHEN date BETWEEN '{this_week_start}' AND '{this_week_end}' THEN cost ELSE 0 END) AS this_week_cost,
    SUM(CASE WHEN date BETWEEN '{prev_week_start}' AND '{prev_week_end}' THEN cost ELSE 0 END) AS prev_week_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date BETWEEN '{prev_week_start}' AND '{this_week_end}'
    {cto_filter}
    {pillar_filter}
    {product_filter}
GROUP BY environment_type