"""Validate, transform, load SQLite, and export Power BI-ready tables."""
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)
DB = OUT / "hospital_analytics.db"

REQUIRED = ["visit_id", "arrival_time", "department", "acuity", "on_duty_staff",
            "registration_minutes", "triage_time", "clinician_start_time",
            "discharge_time", "service_minutes", "outcome"]

def transform_visits(path: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(path)
    missing_cols = sorted(set(REQUIRED) - set(df.columns))
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    before = len(df)
    df = df.drop_duplicates(subset=["visit_id"]).copy()
    for col in ["arrival_time", "triage_time", "clinician_start_time", "discharge_time"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    numeric = ["on_duty_staff", "registration_minutes", "service_minutes"]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["registration_to_triage_minutes"] = (df["triage_time"] - df["arrival_time"]).dt.total_seconds() / 60
    df["triage_to_clinician_minutes"] = (df["clinician_start_time"] - df["triage_time"]).dt.total_seconds() / 60
    df["total_wait_minutes"] = (df["clinician_start_time"] - df["arrival_time"]).dt.total_seconds() / 60
    df["length_of_stay_minutes"] = (df["discharge_time"] - df["arrival_time"]).dt.total_seconds() / 60
    df["arrival_date"] = df["arrival_time"].dt.date.astype("string")
    df["arrival_hour"] = df["arrival_time"].dt.hour
    df["day_of_week"] = df["arrival_time"].dt.day_name()
    df["wait_over_60"] = df["total_wait_minutes"] > 60
    df["wait_over_120"] = df["total_wait_minutes"] > 120
    df["patients_per_staff_proxy"] = 1 / df["on_duty_staff"].clip(lower=1)
    valid = (
        df["visit_id"].notna()
        & df["arrival_time"].notna()
        & df["department"].notna()
        & df["total_wait_minutes"].between(0, 720)
        & df["registration_to_triage_minutes"].between(0, 240)
        & df["length_of_stay_minutes"].between(0, 1440)
        & df["on_duty_staff"].between(1, 100)
    )
    rejected = int((~valid).sum())
    clean = df.loc[valid].copy()
    clean["on_duty_staff"] = clean["on_duty_staff"].astype(int)
    clean["wait_over_60"] = clean["wait_over_60"].astype(bool)
    clean["wait_over_120"] = clean["wait_over_120"].astype(bool)
    quality = {"rows_read": before, "duplicates_removed": before - len(df),
               "invalid_rows_rejected": rejected, "rows_loaded": len(clean)}
    return clean, quality

def aggregate_tables(df: pd.DataFrame):
    hourly = (df.groupby(["arrival_date", "arrival_hour", "department"], as_index=False)
                .agg(patient_visits=("visit_id", "count"),
                     median_wait_minutes=("total_wait_minutes", "median"),
                     p90_wait_minutes=("total_wait_minutes", lambda x: x.quantile(.9)),
                     wait_over_60_count=("wait_over_60", "sum"),
                     avg_staff_on_duty=("on_duty_staff", "mean")))
    hourly["pct_wait_over_60"] = hourly["wait_over_60_count"] / hourly["patient_visits"] * 100
    dept = (df.groupby("department", as_index=False)
              .agg(patient_visits=("visit_id", "count"),
                   median_wait_minutes=("total_wait_minutes", "median"),
                   mean_wait_minutes=("total_wait_minutes", "mean"),
                   p90_wait_minutes=("total_wait_minutes", lambda x: x.quantile(.9)),
                   wait_over_60_count=("wait_over_60", "sum"),
                   avg_staff_on_duty=("on_duty_staff", "mean")))
    dept["pct_wait_over_60"] = dept["wait_over_60_count"] / dept["patient_visits"] * 100
    daily = (df.groupby("arrival_date", as_index=False)
               .agg(patient_visits=("visit_id", "count"),
                    median_wait_minutes=("total_wait_minutes", "median"),
                    p90_wait_minutes=("total_wait_minutes", lambda x: x.quantile(.9)),
                    wait_over_60_count=("wait_over_60", "sum")))
    daily["pct_wait_over_60"] = daily["wait_over_60_count"] / daily["patient_visits"] * 100
    return hourly, dept, daily

def main():
    input_path = RAW / "synthetic_patient_visits.csv"
    if not input_path.exists():
        raise FileNotFoundError("Run `python src/generate_data.py` first.")
    clean, quality = transform_visits(input_path)
    hourly, dept, daily = aggregate_tables(clean)
    with sqlite3.connect(DB) as conn:
        clean.to_sql("visits_clean", conn, if_exists="replace", index=False)
        hourly.to_sql("hourly_metrics", conn, if_exists="replace", index=False)
        dept.to_sql("department_metrics", conn, if_exists="replace", index=False)
        daily.to_sql("daily_metrics", conn, if_exists="replace", index=False)
        conn.executescript((ROOT / "sql" / "views.sql").read_text(encoding="utf-8"))
    clean.to_csv(OUT / "visits_clean.csv", index=False)
    hourly.to_csv(OUT / "hourly_metrics.csv", index=False)
    dept.to_csv(OUT / "department_metrics.csv", index=False)
    daily.to_csv(OUT / "daily_metrics.csv", index=False)
    (OUT / "data_quality_report.json").write_text(__import__("json").dumps(quality, indent=2), encoding="utf-8")
    print("ETL completed.")
    print(f"Quality summary: {quality}")
    print(f"SQLite database: {DB}")
    print(f"Power BI exports: {OUT}")

if __name__ == "__main__":
    main()
