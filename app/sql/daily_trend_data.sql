SELECT
    date,
    environment_type,
    daily_cost,
    fy25_avg_daily_spend,
    fy26_ytd_avg_daily_spend,
    fy26_forecasted_avg_daily_spend
FROM `{project_id}.{dataset}.{avg_table}`
WHERE date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY date