import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# ============================================================
# LOAD FINAL FROZEN MODEL + PREDICTIONS
# ============================================================

model = joblib.load(
    "05_OUTPUTS/final_frozen_random_forest.joblib"
)

predictions = pd.read_csv(
    "05_OUTPUTS/final_frozen_2024_predictions.csv"
)

print("Predictions loaded:", predictions.shape)

# ============================================================
# CLASSIFICATION LABELS
# ============================================================

predictions["classification"] = np.select(
    [
        (
            (predictions["distress_12m"] == 1) &
            (predictions["predicted_distress"] == 1)
        ),
        (
            (predictions["distress_12m"] == 0) &
            (predictions["predicted_distress"] == 0)
        ),
        (
            (predictions["distress_12m"] == 0) &
            (predictions["predicted_distress"] == 1)
        ),
        (
            (predictions["distress_12m"] == 1) &
            (predictions["predicted_distress"] == 0)
        )
    ],
    [
        "True Positive",
        "True Negative",
        "False Positive",
        "False Negative"
    ],
    default="Unknown"
)

# ============================================================
# BASIC ERROR COUNTS
# ============================================================

print("\n--- CLASSIFICATION COUNTS ---")
print(
    predictions["classification"]
    .value_counts()
)

# ============================================================
# FALSE NEGATIVES
# ============================================================

false_negatives = predictions[
    predictions["classification"] == "False Negative"
].sort_values(
    "predicted_probability",
    ascending=False
)

print("\n--- FALSE NEGATIVES ---")
print(
    false_negatives[
        [
            "ticker",
            "company",
            "filed",
            "future_drawdown_12m",
            "predicted_probability"
        ]
    ].to_string(index=False)
)

# ============================================================
# FALSE POSITIVES
# ============================================================

false_positives = predictions[
    predictions["classification"] == "False Positive"
].sort_values(
    "predicted_probability",
    ascending=False
)

print("\n--- FALSE POSITIVES ---")
print(
    false_positives[
        [
            "ticker",
            "company",
            "filed",
            "future_drawdown_12m",
            "predicted_probability"
        ]
    ].to_string(index=False)
)

# ============================================================
# BORDERLINE CASES
# ============================================================

predictions["distance_from_threshold"] = (
    predictions["predicted_probability"] - 0.50
).abs()

borderline = predictions.sort_values(
    "distance_from_threshold"
).head(15)

print("\n--- MOST BORDERLINE CASES ---")
print(
    borderline[
        [
            "ticker",
            "company",
            "filed",
            "distress_12m",
            "future_drawdown_12m",
            "predicted_probability",
            "predicted_distress"
        ]
    ].to_string(index=False)
)

# ============================================================
# PERFORMANCE BY COMPANY
# ============================================================

company_summary = (
    predictions
    .groupby(["ticker", "company"])
    .agg(
        observations=("distress_12m", "size"),
        actual_distress=("distress_12m", "sum"),
        predicted_distress=("predicted_distress", "sum"),
        avg_probability=("predicted_probability", "mean"),
        avg_drawdown=("future_drawdown_12m", "mean")
    )
    .reset_index()
)

print("\n--- COMPANY SUMMARY ---")
print(
    company_summary
    .sort_values(
        "avg_probability",
        ascending=False
    )
    .to_string(index=False)
)

# ============================================================
# SAVE ANALYZED PREDICTIONS
# ============================================================

predictions.to_csv(
    "05_OUTPUTS/final_frozen_2024_predictions_analyzed.csv",
    index=False
)

company_summary.to_csv(
    "05_OUTPUTS/final_frozen_company_summary.csv",
    index=False
)

print("\nAnalyzed predictions saved.")
print("Company summary saved.")