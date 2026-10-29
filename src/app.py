"""Interactive hospital operations dashboard."""
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "hospital_analytics.db"

st.set_page_config(page_title="Hospital Wait-Time Analytics", page_icon="🏥", layout="wide")
st.title("Hospital Patient Waiting-Time Analytics")
st.caption("Operations dashboard • Synthetic patient-level demonstration data • Not for clinical decision-making")

if not DB.exists():
    st.warning("Analytics database not found. In PowerShell, run: python src\\generate_data.py, then python src\\etl.py")
    st.stop()

@st.cache_data
def load_data(db_path):
    with sqlite3.connect(db_path) as conn:
        visits = pd.read_sql_query("SELECT * FROM visits_clean", conn, parse_dates=["arrival_time", "triage_time", "clinician_start_time", "discharge_time"])
        hourly = pd.read_sql_query("SELECT * FROM hourly_metrics", conn)
        dept = pd.read_sql_query("SELECT * FROM department_metrics", conn)
        daily = pd.read_sql_query("SELECT * FROM daily_metrics", conn)
    return visits, hourly, dept, daily

visits, hourly, dept, daily = load_data(str(DB))
visits["arrival_date"] = pd.to_datetime(visits["arrival_date"], errors="coerce")
min_date = visits["arrival_time"].min().date()
max_date = visits["arrival_time"].max().date()

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input("Arrival date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    departments = st.multiselect("Department", sorted(visits["department"].unique()), default=sorted(visits["department"].unique()))
    acuities = st.multiselect("Acuity", sorted(visits["acuity"].unique()), default=sorted(visits["acuity"].unique()))
    wait_threshold = st.slider("Long-wait threshold (minutes)", 30, 180, 60, 15)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

filtered = visits[
    visits["arrival_time"].dt.date.between(start_date, end_date)
    & visits["department"].isin(departments)
    & visits["acuity"].isin(acuities)
].copy()

if filtered.empty:
    st.info("No records match these filters. Adjust the filters in the sidebar.")
    st.stop()

filtered["long_wait"] = filtered["total_wait_minutes"] > wait_threshold
n = len(filtered)
median_wait = filtered["total_wait_minutes"].median()
p90 = filtered["total_wait_minutes"].quantile(.90)
pct_long = 100 * filtered["long_wait"].mean()
avg_staff = filtered["on_duty_staff"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Patient visits", f"{n:,}")
c2.metric("Median wait", f"{median_wait:.0f} min")
c3.metric("90th percentile wait", f"{p90:.0f} min")
c4.metric(f"Waits > {wait_threshold} min", f"{pct_long:.1f}%")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Executive Overview", "Time & Demand", "Departments", "Staffing Scenario", "Data Explorer"])

with tab1:
    left, right = st.columns(2)
    trend = filtered.groupby(filtered["arrival_time"].dt.date, as_index=False).agg(
        visits=("visit_id", "count"), median_wait=("total_wait_minutes", "median"))
    trend = trend.rename(columns={"arrival_time": "date"})
    left.plotly_chart(px.line(trend, x="arrival_time", y="median_wait", markers=True,
                              title="Daily median wait", labels={"arrival_time":"Date","median_wait":"Minutes"}),
                      use_container_width=True)
    by_dept = filtered.groupby("department", as_index=False).agg(
        visits=("visit_id","count"), median_wait=("total_wait_minutes","median"),
        p90_wait=("total_wait_minutes", lambda x: x.quantile(.9)))
    right.plotly_chart(px.bar(by_dept.sort_values("median_wait", ascending=False), x="department", y="median_wait",
                              color="median_wait", title="Median wait by department",
                              labels={"department":"Department","median_wait":"Median wait (min)"}),
                       use_container_width=True)
    st.subheader("Where to investigate first")
    risk = by_dept.sort_values(["p90_wait", "visits"], ascending=False).head(3)
    st.dataframe(risk.rename(columns={"department":"Department","visits":"Visits","median_wait":"Median wait (min)","p90_wait":"P90 wait (min)"}), use_container_width=True, hide_index=True)
    st.caption("These are investigation priorities based on simulated records, not findings about a real hospital.")

with tab2:
    filtered["arrival_hour"] = filtered["arrival_time"].dt.hour
    hourly_view = filtered.groupby("arrival_hour", as_index=False).agg(
        visits=("visit_id","count"), median_wait=("total_wait_minutes","median"),
        avg_staff=("on_duty_staff","mean"), p90_wait=("total_wait_minutes", lambda x: x.quantile(.9)))
    a, b = st.columns(2)
    a.plotly_chart(px.bar(hourly_view, x="arrival_hour", y="visits", title="Arrivals by hour",
                          labels={"arrival_hour":"Hour of day","visits":"Visits"}), use_container_width=True)
    b.plotly_chart(px.line(hourly_view, x="arrival_hour", y="median_wait", markers=True,
                           title="Median wait by arrival hour",
                           labels={"arrival_hour":"Hour of day","median_wait":"Minutes"}), use_container_width=True)
    st.plotly_chart(px.scatter(hourly_view, x="visits", y="median_wait", size="p90_wait",
                               hover_data=["arrival_hour","avg_staff"], title="Demand vs median wait",
                               labels={"visits":"Visits in hour","median_wait":"Median wait (min)"}),
                    use_container_width=True)

with tab3:
    summary = filtered.groupby("department", as_index=False).agg(
        visits=("visit_id","count"), median_wait=("total_wait_minutes","median"),
        mean_wait=("total_wait_minutes","mean"), p90_wait=("total_wait_minutes",lambda x:x.quantile(.9)),
        avg_staff=("on_duty_staff","mean"), long_waits=("long_wait","sum"))
    summary["long_wait_pct"] = 100 * summary["long_waits"] / summary["visits"]
    st.dataframe(summary.round(1).rename(columns={
        "department":"Department","visits":"Visits","median_wait":"Median wait (min)",
        "mean_wait":"Mean wait (min)","p90_wait":"P90 wait (min)","avg_staff":"Avg staff",
        "long_waits":"Long waits","long_wait_pct":"Long waits (%)"}), use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(summary.sort_values("long_wait_pct", ascending=False), x="department", y="long_wait_pct",
                           title=f"Share of visits waiting over {wait_threshold} minutes",
                           labels={"department":"Department","long_wait_pct":"Visits (%)"}),
                    use_container_width=True)

with tab4:
    st.markdown("### Illustrative capacity scenario")
    st.write("Estimate how additional staff could change nominal service capacity. This is a simple what-if model, not a queueing simulation or staffing recommendation.")
    left, right = st.columns(2)
    with left:
        additional_staff = st.slider("Additional staff per peak hour", 0, 10, 2)
        patients_per_staff_hour = st.slider("Assumed patients handled per staff-hour", 1, 8, 3)
        selected_dept = st.selectbox("Department for scenario", sorted(filtered["department"].unique()))
    sub = filtered[filtered["department"] == selected_dept].copy()
    sub["hour"] = sub["arrival_time"].dt.floor("h")
    demand = sub.groupby("hour").size().rename("arrivals").reset_index()
    demand["current_staff"] = sub.groupby("hour")["on_duty_staff"].mean().values
    demand["scenario_capacity"] = (demand["current_staff"] + additional_staff) * patients_per_staff_hour
    demand["capacity_gap"] = demand["arrivals"] - demand["scenario_capacity"]
    total_arrivals = int(demand["arrivals"].sum())
    total_capacity = float(demand["scenario_capacity"].sum())
    with right:
        st.metric("Visits in selected department", f"{total_arrivals:,}")
        st.metric("Estimated hourly capacity", f"{total_capacity:,.0f} patient-slots")
        st.metric("Hours where arrivals exceed scenario capacity", f"{int((demand['capacity_gap'] > 0).sum()):,}")
    st.plotly_chart(px.line(demand, x="hour", y=["arrivals","scenario_capacity"], title="Hourly arrivals vs scenario capacity",
                           labels={"hour":"Hour","value":"Patients / patient-slots","variable":"Series"}),
                    use_container_width=True)
    st.caption("Capacity assumptions are user-entered. Validate service rates, breaks, acuity mix, skill mix, and local policy before real-world use.")

with tab5:
    st.markdown("### Filtered visit records")
    show_cols = ["visit_id","arrival_time","department","acuity","on_duty_staff",
                 "registration_to_triage_minutes","triage_to_clinician_minutes",
                 "total_wait_minutes","length_of_stay_minutes","outcome"]
    st.dataframe(filtered[show_cols].sort_values("total_wait_minutes", ascending=False),
                 use_container_width=True, hide_index=True)
    st.download_button("Download filtered records (CSV)", filtered[show_cols].to_csv(index=False).encode("utf-8"),
                       file_name="filtered_hospital_waits.csv", mime="text/csv")
    st.markdown("### Data quality snapshot")
    st.json({"records_loaded": int(len(visits)), "records_after_filters": int(len(filtered)),
             "missing_total_wait": int(visits["total_wait_minutes"].isna().sum()),
             "synthetic_data": True})
