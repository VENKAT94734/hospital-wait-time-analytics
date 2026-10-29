-- 1. Department-level wait performance
SELECT department, COUNT(*) AS visits,
       ROUND(AVG(total_wait_minutes), 1) AS avg_wait,
       SUM(CASE WHEN total_wait_minutes > 60 THEN 1 ELSE 0 END) AS waits_over_60
FROM visits_clean
GROUP BY department
ORDER BY avg_wait DESC;

-- 2. Hourly arrival demand and average staffing
SELECT arrival_hour, department, COUNT(*) AS visits,
       ROUND(AVG(on_duty_staff), 1) AS avg_staff,
       ROUND(AVG(total_wait_minutes), 1) AS avg_wait
FROM visits_clean
GROUP BY arrival_hour, department
ORDER BY department, arrival_hour;

-- 3. Acuity and wait relationship (descriptive, not causal)
SELECT acuity, COUNT(*) AS visits,
       ROUND(AVG(total_wait_minutes), 1) AS avg_wait,
       ROUND(1.0 * SUM(CASE WHEN total_wait_minutes > 60 THEN 1 ELSE 0 END) / COUNT(*) * 100, 1) AS pct_over_60
FROM visits_clean
GROUP BY acuity;

-- 4. Longest waits to inspect (synthetic data only)
SELECT visit_id, arrival_time, department, acuity, total_wait_minutes
FROM visits_clean
ORDER BY total_wait_minutes DESC
LIMIT 25;
