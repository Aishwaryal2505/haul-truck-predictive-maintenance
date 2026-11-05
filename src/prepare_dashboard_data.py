"""
Step 4: Prepare data for the Power BI dashboard.

Reads data/truck_risk_scores.csv (made by train_model.py) and creates two files:
  1. data/dashboard_daily.csv   -> one row per truck per day, with a risk level
  2. data/dashboard_latest.csv  -> one row per truck: its most recent risk, ranked
"""

import pandas as pd

df = pd.read_csv("data/truck_risk_scores.csv", parse_dates=["date"])

# Turn the 0-1 score into a simple label a manager can read.
# These cut-offs are choices you can change (see the recall/precision table).
def risk_level(score):
    if score >= 0.5:
        return "High"
    if score >= 0.3:
        return "Medium"
    return "Low"

df["risk_level"] = df["risk_score"].apply(risk_level)
df["risk_percent"] = (df["risk_score"] * 100).round(0)

# ---------- File 1: every truck, every day ----------
daily_cols = [
    "truck_id", "date", "risk_score", "risk_percent", "risk_level",
    "vibration", "vibration_7d_avg", "vibration_trend",
    "hours_since_service", "truck_age_years", "downtimes_30d",
]
daily = df[daily_cols]
daily.to_csv("data/dashboard_daily.csv", index=False)

# ---------- File 2: latest day for each truck ----------
latest = (
    df.sort_values("date")
      .groupby("truck_id")
      .tail(1)                                   # last row of each truck
      .sort_values("risk_score", ascending=False)
      [daily_cols]
)
latest.to_csv("data/dashboard_latest.csv", index=False)

print(f"Saved data/dashboard_daily.csv   ({len(daily)} rows)")
print(f"Saved data/dashboard_latest.csv  ({len(latest)} rows, one per truck)")
print()
print("Latest day:", latest["date"].max().date())
print("Trucks by risk level on the latest day:")
print(latest["risk_level"].value_counts().to_string())
print()
print("Top 5 highest-risk trucks right now:")
print(latest.head(5)[["truck_id", "risk_percent", "risk_level",
                      "vibration_7d_avg", "vibration_trend",
                      "hours_since_service"]].to_string(index=False))
