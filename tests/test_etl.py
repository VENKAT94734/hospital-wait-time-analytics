import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from etl import transform_visits, aggregate_tables

def test_transform_and_aggregate(tmp_path):
    rows = [{
        "visit_id":"V1", "arrival_time":"2025-01-01 10:00:00", "department":"Emergency",
        "acuity":"Urgent", "on_duty_staff":5, "registration_minutes":5,
        "triage_time":"2025-01-01 10:05:00", "clinician_start_time":"2025-01-01 10:35:00",
        "discharge_time":"2025-01-01 11:00:00", "service_minutes":25, "outcome":"Discharged"
    }]
    p = tmp_path / "visits.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    clean, quality = transform_visits(p)
    assert len(clean) == 1
    assert clean.iloc[0]["total_wait_minutes"] == 35
    assert quality["rows_loaded"] == 1
    hourly, dept, daily = aggregate_tables(clean)
    assert dept.iloc[0]["patient_visits"] == 1
    assert hourly.iloc[0]["patient_visits"] == 1
    assert daily.iloc[0]["patient_visits"] == 1

def test_invalid_negative_wait_rejected(tmp_path):
    rows = [{
        "visit_id":"V2", "arrival_time":"2025-01-01 10:00:00", "department":"Emergency",
        "acuity":"Routine", "on_duty_staff":5, "registration_minutes":5,
        "triage_time":"2025-01-01 10:05:00", "clinician_start_time":"2025-01-01 09:55:00",
        "discharge_time":"2025-01-01 11:00:00", "service_minutes":25, "outcome":"Discharged"
    }]
    p = tmp_path / "bad.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    clean, quality = transform_visits(p)
    assert clean.empty
    assert quality["invalid_rows_rejected"] == 1
