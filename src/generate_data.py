"""Generate reproducible synthetic hospital visit and hourly staffing data."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

def generate_visits(n: int = 12000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2025-01-01")
    day_offsets = rng.integers(0, 365, n)
    # Mixture of arrival times creates realistic peak-hour patterns.
    hour_choices = rng.choice([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
                              size=n, p=np.array([.025,.045,.07,.08,.08,.08,.075,.075,.075,.075,.07,.065,.055,.045,.03,.02]) / sum([.025,.045,.07,.08,.08,.08,.075,.075,.075,.075,.07,.065,.055,.045,.03,.02]))
    minute = rng.integers(0, 60, n)
    arrivals = pd.to_datetime(start + pd.to_timedelta(day_offsets, unit="D")) + pd.to_timedelta(hour_choices, unit="h") + pd.to_timedelta(minute, unit="m")
    departments = np.array(["Emergency", "General Medicine", "Orthopedics", "Cardiology", "Pediatrics", "Outpatient"])
    dep_probs = np.array([0.31, 0.22, 0.13, 0.10, 0.09, 0.10]) / sum([0.31, 0.22, 0.13, 0.10, 0.09, 0.10])
    dept = rng.choice(departments, n, p=dep_probs)
    acuity = rng.choice(["Routine", "Urgent", "High"], n, p=[.54, .36, .10])
    weekend = pd.Series(arrivals).dt.dayofweek.to_numpy() >= 5
    hour = pd.Series(arrivals).dt.hour.to_numpy()
    # Staff coverage is lower in overnight/early hours; volumes are higher in late morning.
    staff_base = np.select([hour < 8, hour < 12, hour < 17, hour < 21],
                           [3, 7, 8, 6], default=4)
    dept_adjust = pd.Series(dept).map({"Emergency": 2, "General Medicine": 1, "Orthopedics": 0,
                                       "Cardiology": 0, "Pediatrics": 0, "Outpatient": -1}).to_numpy()
    staff = np.maximum(1, staff_base + dept_adjust - weekend.astype(int) + rng.integers(-1, 2, n))
    # Base waits are affected by department, acuity, hour demand, weekend, and staffing pressure.
    dep_delay = pd.Series(dept).map({"Emergency": 24, "General Medicine": 18, "Orthopedics": 20,
                                     "Cardiology": 25, "Pediatrics": 14, "Outpatient": 12}).to_numpy()
    peak_effect = np.where((hour >= 10) & (hour <= 15), 14, 0)
    weekend_effect = weekend.astype(int) * 8
    acuity_effect = pd.Series(acuity).map({"Routine": 12, "Urgent": 3, "High": -8}).to_numpy()
    demand_noise = rng.gamma(shape=2.0, scale=8.0, size=n)
    wait = np.clip(dep_delay + peak_effect + weekend_effect + acuity_effect + demand_noise
                   + (7 - np.minimum(staff, 7)) * 3 + rng.normal(0, 8, n), 3, 300).round().astype(int)
    registration = rng.integers(2, 13, n)
    triage = arrivals + pd.to_timedelta(registration, unit="m")
    clinician = triage + pd.to_timedelta(wait, unit="m")
    service = np.clip(rng.gamma(2.2, 18, n) + pd.Series(acuity).map({"Routine": 0, "Urgent": 10, "High": 22}).to_numpy(), 8, 180).round().astype(int)
    discharge = clinician + pd.to_timedelta(service, unit="m")
    outcome = rng.choice(["Discharged", "Admitted", "Transferred", "Left before assessment"], n, p=[.72,.16,.07,.05])
    frame = pd.DataFrame({
        "visit_id": [f"VIS{idx:07d}" for idx in range(1, n + 1)],
        "arrival_time": arrivals,
        "department": dept,
        "acuity": acuity,
        "on_duty_staff": staff,
        "registration_minutes": registration,
        "triage_time": triage,
        "clinician_start_time": clinician,
        "discharge_time": discharge,
        "service_minutes": service,
        "outcome": outcome,
        "is_weekend": weekend
    })
    return frame.sort_values("arrival_time").reset_index(drop=True)

def generate_staffing(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hours = pd.date_range("2025-01-01", "2025-12-31 23:00:00", freq="h")
    rows = []
    for ts in hours:
        for dep in ["Emergency", "General Medicine", "Orthopedics", "Cardiology", "Pediatrics", "Outpatient"]:
            h = ts.hour
            base = 3 if h < 8 or h >= 21 else (7 if h < 12 else 8 if h < 17 else 6)
            adjustment = {"Emergency": 2, "General Medicine": 1, "Orthopedics": 0, "Cardiology": 0, "Pediatrics": 0, "Outpatient": -1}[dep]
            staff = max(1, base + adjustment - int(ts.dayofweek >= 5) + int(rng.integers(-1, 2)))
            rows.append((ts, dep, staff))
    return pd.DataFrame(rows, columns=["hour_start", "department", "staff_on_duty"])

if __name__ == "__main__":
    visits = generate_visits()
    staffing = generate_staffing()
    visits.to_csv(RAW / "synthetic_patient_visits.csv", index=False)
    staffing.to_csv(RAW / "synthetic_hourly_staffing.csv", index=False)
    print(f"Generated {len(visits):,} synthetic visits.")
    print(f"Generated {len(staffing):,} synthetic department-hour staffing rows.")
    print(f"Output: {RAW}")
