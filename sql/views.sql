DROP VIEW IF EXISTS vw_department_wait_summary;
CREATE VIEW vw_department_wait_summary AS
SELECT department,
       COUNT(*) AS patient_visits,
       ROUND(AVG(total_wait_minutes), 1) AS mean_wait_minutes,
       ROUND(1.0 * (SELECT total_wait_minutes FROM visits_clean v2
         WHERE v2.department = v.department
         ORDER BY total_wait_minutes LIMIT 1 OFFSET
         (SELECT CAST(COUNT(*) * 0.5 AS INT) FROM visits_clean v3 WHERE v3.department = v.department)), 1) AS approximate_median_wait_minutes,
       SUM(CASE WHEN total_wait_minutes > 60 THEN 1 ELSE 0 END) AS waits_over_60,
       ROUND(100.0 * SUM(CASE WHEN total_wait_minutes > 60 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_wait_over_60
FROM visits_clean v
GROUP BY department;

DROP VIEW IF EXISTS vw_hourly_demand;
CREATE VIEW vw_hourly_demand AS
SELECT arrival_hour, department,
       COUNT(*) AS patient_visits,
       ROUND(AVG(total_wait_minutes), 1) AS avg_wait_minutes,
       ROUND(AVG(on_duty_staff), 1) AS avg_staff_on_duty,
       ROUND(1.0 * COUNT(*) / AVG(on_duty_staff), 2) AS demand_per_staff_proxy
FROM visits_clean
GROUP BY arrival_hour, department;

DROP VIEW IF EXISTS vw_long_waits;
CREATE VIEW vw_long_waits AS
SELECT visit_id, arrival_time, department, acuity, on_duty_staff,
       total_wait_minutes, length_of_stay_minutes, outcome
FROM visits_clean
WHERE total_wait_minutes > 60;
