-- Basic day-to-day comparison query
SELECT
    CASE 
        WHEN environment LIKE 'PROD%' THEN 'PROD'
        WHEN environment LIKE '%NON-PROD%' THEN 'NON-PROD'
        ELSE 'OTHER'
    END AS environment_type,
    SUM(CASE WHEN date = '{day_current}' THEN cost ELSE 0 END) AS day_current_cost,
    SUM(CASE WHEN date = '{day_previous}' THEN cost ELSE 0 END) AS day_previous_cost
FROM `{project_id}.{dataset}.{table}`
WHERE date IN ('{day_current}', '{day_previous}')
GROUP BY environment_type