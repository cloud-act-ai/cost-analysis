WITH this_week AS (
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '{this_week_start}' AND '{this_week_end}'
    GROUP BY environment_type
),
prev_week AS (
    SELECT
        CASE 
            WHEN environment LIKE '%PROD%' THEN 'PROD'
            ELSE 'NON-PROD'
        END AS environment_type,
        SUM(cost) AS total_cost
    FROM `{project_id}.{dataset}.{table}`
    WHERE date BETWEEN '{prev_week_start}' AND '{prev_week_end}'
    GROUP BY environment_type
)
SELECT
    tw.environment_type,
    tw.total_cost AS this_week_cost,
    pw.total_cost AS prev_week_cost,
    (tw.total_cost - pw.total_cost) / NULLIF(pw.total_cost, 0) * 100 AS percent_change
FROM this_week tw
JOIN prev_week pw ON tw.environment_type = pw.environment_type