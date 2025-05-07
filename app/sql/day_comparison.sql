WITH current_day AS (
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost,
        '{day_current}' AS compare_date
    FROM `{project_id}.{dataset}.{table}`
    WHERE date = '{day_current}'
    GROUP BY environment_type
),
previous_day AS (
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE date = '{day_previous}'
    GROUP BY environment_type
)
SELECT
    current.environment_type,
    current.total_cost AS day_current_cost,
    prev.total_cost AS day_previous_cost,
    current.compare_date AS compare_date,
    (current.total_cost - prev.total_cost) / NULLIF(prev.total_cost, 0) * 100 AS percent_change
FROM current_day current
JOIN previous_day prev ON current.environment_type = prev.environment_type