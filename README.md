# Hospital Patient Waiting-Time Analytics & Workforce Optimization

A portfolio-ready analytics system for understanding patient flow, operational bottlenecks, and staff-demand alignment. Includes a reproducible Python ETL pipeline, SQLite database, SQL KPI views, Streamlit dashboard, automated tests, and Power BI-ready exports.

> **Data integrity:** The included patient-level dataset is synthetic and generated locally. It contains no real patient records or personal medical information. Public NHS England data is available as an optional real-world *aggregated benchmark*; it does not contain the patient-level timestamps needed to calculate individual waits. Do not combine synthetic patient-level records and real aggregate statistics as if they were one dataset.

## Features
- Generates 12,000 reproducible synthetic visit records across departments and a full year.
- Validates required fields, timestamps, wait-time bounds, and duplicate visit IDs.
- Computes registration-to-triage, triage-to-clinician, and total waiting time.
- Loads clean data into SQLite and creates SQL views for hourly, department, and staffing analysis.
- Provides interactive Streamlit dashboard filters and a staffing scenario calculator.
- Exports cleaned CSV files for Power BI and Excel.
- Includes SQL examples, tests, and clear data dictionary.

## Architecture
`Synthetic CSV / Optional public aggregates -> Python validation & ETL -> SQLite + CSV exports -> SQL analysis -> Streamlit / Power BI`

## Quick start (Windows PowerShell)
1. Install Python 3.10+ from https://www.python.org/downloads/ and check **Add Python to PATH**.
2. Extract the ZIP file, open PowerShell in the project folder.
3. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Generate the synthetic dataset:

```powershell
python src\generate_data.py
```

5. Run ETL, create the SQLite database, and export Power BI-ready tables:

```powershell
python src\etl.py
```

6. Start the dashboard:

```powershell
streamlit run src\app.py
```

The dashboard opens in your browser (normally `http://localhost:8501`).

7. Run tests:

```powershell
python -m pytest -q
```

## Public real-world data source (optional)
NHS England publishes monthly A&E attendances, emergency admissions, and four-hour performance at provider/system level. These are real operational statistics, but they are **aggregated**, not encounter-level timestamps.

- Official landing page: https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/
- Current monthly publication page: https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2026-27/

Download a CSV/XLS from the official page. Use `data/raw/nhs_aggregate_data/` to store it locally and document its source, publication month, and units. The included app does not silently ingest it because the NHS files' schemas vary by publication. The project intentionally keeps the operational patient-level demo separate from public aggregate benchmark data.

A fully synthetic public dataset that can be explored separately is also described at:
https://huggingface.co/datasets/AuricGrid-Laboratory/E3.H2-Synthetic_Hospital_Operations_Environment
Check the dataset's license and schema before reuse.

## Dashboard pages
- **Overview:** total visits, median wait, 90th percentile wait, percentage over 60 minutes, trend and department comparison.
- **Time & Demand:** arrivals and waits by hour/day, peak demand periods.
- **Department Analysis:** volume, median and P90 wait, long-wait percentage.
- **Staffing Scenario:** adjustable additional staff and estimated service capacity. This is a simplified planning scenario, not a validated staffing recommendation.
- **Data Quality:** input counts, invalid rows, and ETL status.

## Key definitions
- `total_wait_minutes`: arrival to clinician start, based on the synthetic timestamps.
- `wait_over_60`: whether total wait exceeds 60 minutes.
- `p90_wait_minutes`: 90th percentile total wait; useful because the mean can hide very long waits.
- `patients_per_staff`: arrivals divided by on-duty staff for the hour. This is a demand pressure indicator, not a clinical workload measure.
- `capacity_scenario`: illustrative estimate based on configurable average patients handled per staff-hour; do not use for live clinical decisions without local validation.

## Power BI
After running ETL, import:
- `data/processed/visits_clean.csv`
- `data/processed/hourly_metrics.csv`
- `data/processed/department_metrics.csv`
- `data/processed/daily_metrics.csv`

Recommended report pages:
1. Executive Overview
2. Department Bottlenecks
3. Hourly Demand & Staffing
4. Data Quality / Definitions

Useful DAX measures (rename table to `visits_clean`):
```DAX
Total Visits = COUNTROWS(visits_clean)
Median Wait (min) = MEDIAN(visits_clean[total_wait_minutes])
P90 Wait (min) = PERCENTILE.INC(visits_clean[total_wait_minutes], 0.9)
Waits Over 60 Min = CALCULATE(COUNTROWS(visits_clean), visits_clean[total_wait_minutes] > 60)
% Waits Over 60 Min = DIVIDE([Waits Over 60 Min], [Total Visits], 0)
```

## GitHub publishing checklist
- Include README, source code, SQL, tests, and a small synthetic CSV.
- Do not upload any real patient data, secrets, credentials, or private hospital exports.
- Add a clear banner that the included patient-level data is synthetic.
- Add screenshots of your dashboard after running it.
- Suggested repository name: `hospital-wait-time-analytics`.

## Limitations
This is a portfolio demonstration, not a clinical decision-support product. Simulated waits are designed to exercise the analysis workflow; they are not evidence about a real hospital. Correlation and dashboard patterns do not establish causation. The staffing calculator is intentionally simple and must not be used to set actual staffing without expert validation.
