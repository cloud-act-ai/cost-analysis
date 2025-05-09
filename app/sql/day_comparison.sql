-- Basic day-to-day comparison query
SELECT
    CASE 
        WHEN environment = 'PROD' THEN 'PROD'
        ELSE 'NON-PROD'
    END AS environment_type,
    SUM(CASE WHEN date = '{day_current}' THEN cost ELSE 0 END) AS day_current_cost,
    SUM(CASE WHEN date = '{day_previous}' THEN cost ELSE 0 END) AS day_previous_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date IN ('{day_current}', '{day_previous}')
GROUP BY environment_type