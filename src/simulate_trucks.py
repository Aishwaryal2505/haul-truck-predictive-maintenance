"""
Step 1: Simulate haul truck data.

Creates one row per truck per day and saves it to data/truck_data.csv.

How the fake world works:
- Each truck has breakdowns scheduled at random. Older trucks break down more often.
- In the ~14 days BEFORE most breakdowns, vibration climbs (a part is wearing out).
- Some breakdowns (about 20%) are sudden, with no warning. Real life is like that,
  and it means the model can never catch everything.
- Vibration also drifts up with hours since the last service, plus random noise.
The model will later try to discover these patterns on its own.
"""

import numpy as np
import pandas as pd

np.random.seed(42)  # same "random" data every run, so results are repeatable

NUM_TRUCKS = 20
NUM_DAYS = 365
HOURS_PER_DAY = 18        # a truck works about 18 hours a day
SERVICE_EVERY = 500       # planned service every 500 engine hours
FORECAST_DAYS = 14        # label = "fails within the next 14 days?"
WARNING_SHARE = 0.8       # share of breakdowns that show warning signs first

start_date = pd.Timestamp("2025-01-01")
rows = []

for t in range(1, NUM_TRUCKS + 1):
    truck_id = f"HT-{t:02d}"
    age_years = np.random.randint(1, 11)              # 1 to 10 years old
    hours_since_service = np.random.randint(0, SERVICE_EVERY)

    # Schedule this truck's breakdowns. Older trucks -> shorter gaps.
    avg_gap = 130 - 7 * age_years
    failures = {}   # day number -> (has_warning, warning_strength)
    day = np.random.randint(20, avg_gap)
    while day < NUM_DAYS:
        has_warning = np.random.rand() < WARNING_SHARE
        strength = np.random.uniform(0.8, 1.8)
        failures[day] = (has_warning, strength)
        day += np.random.randint(int(avg_gap * 0.6), int(avg_gap * 1.4))

    for d in range(NUM_DAYS):
        date = start_date + pd.Timedelta(days=d)
        hours_since_service += HOURS_PER_DAY

        # planned service resets the counter
        if hours_since_service >= SERVICE_EVERY:
            hours_since_service = 0

        # normal vibration: baseline + wear since service + age + noise
        vibration = (
            2.0
            + 0.002 * hours_since_service
            + 0.05 * age_years
            + np.random.normal(0, 0.3)
        )

        # warning ramp: vibration climbs in the days before a breakdown
        for fday, (has_warning, strength) in failures.items():
            days_to_failure = fday - d
            if has_warning and 0 < days_to_failure <= FORECAST_DAYS:
                vibration += strength * (1 - days_to_failure / FORECAST_DAYS)

        failed_today = d in failures

        rows.append({
            "truck_id": truck_id,
            "date": date,
            "truck_age_years": age_years,
            "hours_since_service": hours_since_service,
            "vibration": round(vibration, 2),
            "failure_today": int(failed_today),
        })

        # a breakdown means repair, which also resets the service counter
        if failed_today:
            hours_since_service = 0

df = pd.DataFrame(rows)

# Build the label: did this truck fail at any point in the NEXT 14 days?
df = df.sort_values(["truck_id", "date"]).reset_index(drop=True)
df["failed_next_14d"] = 0
for truck_id, group in df.groupby("truck_id"):
    fail = group["failure_today"].values
    label = np.zeros(len(fail), dtype=int)
    for i in range(len(fail)):
        label[i] = int(fail[i + 1 : i + 1 + FORECAST_DAYS].any())
    df.loc[group.index, "failed_next_14d"] = label

df.to_csv("data/truck_data.csv", index=False)

print(f"Saved {len(df)} rows to data/truck_data.csv")
print(f"Total breakdowns: {df['failure_today'].sum()}")
print(f"Share of rows labelled 'will fail within 14 days': "
      f"{df['failed_next_14d'].mean():.1%}")
print(df.head())
