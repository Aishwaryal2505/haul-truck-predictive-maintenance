"""
Step 2: Build features.

Reads data/truck_data.csv (raw daily data) and adds columns that describe
each truck's RECENT HISTORY. Saves the result to data/truck_features.csv.
"""

import pandas as pd

df = pd.read_csv("data/truck_data.csv", parse_dates=["date"])
df = df.sort_values(["truck_id", "date"]).reset_index(drop=True)

# Each truck is processed separately so one truck's history never leaks
# into another's.
by_truck = df.groupby("truck_id")

# Average vibration over the last 7 days (including today)
df["vibration_7d_avg"] = by_truck["vibration"].transform(
    lambda s: s.rolling(7).mean()
)

# Is vibration rising? Compare this week's average to last week's.
df["vibration_trend"] = by_truck["vibration_7d_avg"].transform(
    lambda s: s - s.shift(7)
)

# Number of breakdowns in the last 30 days
df["downtimes_30d"] = by_truck["failure_today"].transform(
    lambda s: s.rolling(30, min_periods=1).sum()
)

# The first ~14 days of each truck don't have enough history to calculate
# the trend, so we drop them.
before = len(df)
df = df.dropna().reset_index(drop=True)
print(f"Dropped {before - len(df)} rows with not enough history")

# Keep only the columns the model needs, plus the answer (label)
feature_cols = [
    "truck_id", "date",
    "truck_age_years", "hours_since_service",
    "vibration", "vibration_7d_avg", "vibration_trend", "downtimes_30d",
    "failed_next_14d",
]
df = df[feature_cols]

df.to_csv("data/truck_features.csv", index=False)

print(f"Saved {len(df)} rows to data/truck_features.csv")
print(f"Share labelled 'will fail within 14 days': {df['failed_next_14d'].mean():.1%}")
print(df.head())
