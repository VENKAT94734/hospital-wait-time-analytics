# Data Dictionary

## `synthetic_patient_visits.csv` / `visits_clean`
| Field | Meaning |
|---|---|
| visit_id | Synthetic unique visit key; not a real patient identifier |
| arrival_time | Arrival timestamp |
| department | Simulated service department |
| acuity | Simulated priority category: Routine, Urgent, High |
| on_duty_staff | Simulated department staff available at arrival |
| registration_minutes | Minutes from arrival to triage in generated data |
| triage_time | Arrival plus registration/triage duration |
| clinician_start_time | Simulated start of clinician assessment |
| discharge_time | Simulated end of visit |
| service_minutes | Simulated service duration |
| outcome | Simulated disposition |
| is_weekend | Whether arrival occurred Saturday/Sunday |
| registration_to_triage_minutes | Derived interval |
| triage_to_clinician_minutes | Derived interval |
| total_wait_minutes | Arrival to clinician start |
| length_of_stay_minutes | Arrival to discharge |
| arrival_date | Arrival calendar date |
| arrival_hour | Arrival hour, 0–23 |
| day_of_week | Weekday name |
| wait_over_60 / wait_over_120 | Threshold flags |
| patients_per_staff_proxy | A simple inverse staffing proxy; not a true workload measure |

## `synthetic_hourly_staffing.csv`
- `hour_start`: hour bucket
- `department`: department
- `staff_on_duty`: simulated staffing level

All included patient-level data is synthetic. Do not treat these rows as actual patient records.
