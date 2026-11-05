"""
Step 3: Train the model and check how good it is.

Reads data/truck_features.csv, trains a model on the EARLIER days,
tests it on the LATER days it has never seen, and prints the results.
Also saves a risk score for every test row to data/truck_risk_scores.csv
(we'll use this file for the Power BI dashboard later).
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, precision_score, recall_score

# ---------- 1. Load the data ----------
df = pd.read_csv("data/truck_features.csv", parse_dates=["date"])

# The columns the model is allowed to look at (the clues)
FEATURES = [
    "truck_age_years",
    "hours_since_service",
    "vibration",
    "vibration_7d_avg",
    "vibration_trend",
    "downtimes_30d",
]
# The column the model must predict (the answer)
LABEL = "failed_next_14d"

# ---------- 2. Split into "practice" and "exam" ----------
# First 75% of the days = practice (train). Last 25% = exam (test).
# We split by DATE because in real life you predict the future from the past.
cutoff_date = df["date"].sort_values().iloc[int(len(df) * 0.75)]
train = df[df["date"] < cutoff_date]
test = df[df["date"] >= cutoff_date]

print(f"Practice rows: {len(train)}   Exam rows: {len(test)}")
print(f"Exam starts on: {cutoff_date.date()}\n")

# ---------- 3. Train the model ----------
model = RandomForestClassifier(
    n_estimators=200,         # 200 small decision trees that vote together
    min_samples_leaf=5,       # stops it memorising individual rows
    class_weight="balanced",  # treats rare breakdowns as important
    random_state=42,
)
model.fit(train[FEATURES], train[LABEL])

# ---------- 4. Take the exam ----------
# risk_score = the model's estimated chance (0 to 1) of failure within 14 days
test = test.copy()
test["risk_score"] = model.predict_proba(test[FEATURES])[:, 1]

# ---------- 5. Mark the exam in mechanic language ----------
print("How the results change depending on how jumpy we make the model:")
print("(flag a truck when its risk score is above the threshold)\n")
print(f"{'Threshold':>10} {'Trucks flagged':>15} {'Caught':>8} {'Missed':>8} "
      f"{'False alarms':>13} {'Recall':>8} {'Precision':>10}")

for threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:
    flagged = (test["risk_score"] >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(test[LABEL], flagged).ravel()
    recall = recall_score(test[LABEL], flagged)
    precision = precision_score(test[LABEL], flagged, zero_division=0)
    print(f"{threshold:>10} {flagged.sum():>15} {tp:>8} {fn:>8} {fp:>13} "
          f"{recall:>8.0%} {precision:>10.0%}")

# ---------- 6. Which clues did the model find most useful? ----------
print("\nWhich clues mattered most to the model:")
importance = pd.Series(model.feature_importances_, index=FEATURES)
for name, value in importance.sort_values(ascending=False).items():
    print(f"  {name:<22} {value:.0%}")

# ---------- 7. Save risk scores for the dashboard ----------
test.to_csv("data/truck_risk_scores.csv", index=False)
print("\nSaved data/truck_risk_scores.csv")
