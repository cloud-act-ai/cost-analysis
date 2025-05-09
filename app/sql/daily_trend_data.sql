-- Basic daily trend data query
SELECT
    date,
    CASE
        WHEN environment_type LIKE 'PROD%' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    daily_cost
FROM `{project_id}.{dataset}.{avg_table}`
WHERE date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY date, environment_type