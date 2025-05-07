WITH this_month AS (
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '{this_month_start}' AND '{this_month_end}'
    GROUP BY environment_type
),
prev_month AS (
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '{prev_month_start}' AND '{prev_month_end}'
    GROUP BY environment_type
)
SELECT
    tm.environment_type,
    tm.total_cost AS this_month_cost,
    pm.total_cost AS prev_month_cost,
    (tm.total_cost - pm.total_cost) / NULLIF(pm.total_cost, 0) * 100 AS percent_change
FROM this_month tm
JOIN prev_month pm ON tm.environment_type = pm.environment_type