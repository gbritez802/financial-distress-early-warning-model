import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

from sqlalchemy import create_engine
from getpass import getpass

from sklearn.metrics import (
    roc_curve,
    precision_recall_curve,
    roc_auc_score,
    average_precision_score
)

# ============================================================
# LOAD SAVED MODEL AND PREDICTIONS
# ============================================================

model = joblib.load(
    "05_OUTPUTS/final_random_forest_model.joblib"
)

predictions = pd.read_csv(
    "05_OUTPUTS/final_2024_predictions.csv"
)

print("Saved model loaded.")
print("Predictions loaded:", predictions.shape)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

features = [
    "current_ratio",
    "liabilities_to_assets",
    "return_on_assets",
    "operating_margin",
    "cash_to_assets",
    "revenue_growth_yoy",
    "net_income_growth_yoy",
    "operating_margin_change_yoy",
    "leverage_change_yoy",
    "current_ratio_change_yoy",
    "cash_to_assets_change_yoy",
    "return_on_assets_change_yoy"
]

forest = model.named_steps["classifier"]

importance = pd.DataFrame({
    "feature": features,
    "importance": forest.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\n--- FINAL FEATURE IMPORTANCE ---")
print(importance.to_string(index=False))

importance.to_csv(
    "05_OUTPUTS/final_feature_importance.csv",
    index=False
)


# ============================================================
# ROC CURVE
# ============================================================

y_true = predictions["distress_12m"]
y_probability = predictions["predicted_probability"]

roc_auc = roc_auc_score(
    y_true,
    y_probability
)

fpr, tpr, _ = roc_curve(
    y_true,
    y_probability
)

plt.figure(figsize=(8, 6))

plt.plot(
    fpr,
    tpr,
    label=f"Random Forest (AUC = {roc_auc:.3f})"
)

plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    label="Random classifier"
)

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("2024 Out-of-Sample ROC Curve")
plt.legend()
plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/roc_curve_2024.png",
    dpi=300
)

plt.close()


# ============================================================
# PRECISION-RECALL CURVE
# ============================================================

precision, recall, _ = precision_recall_curve(
    y_true,
    y_probability
)

pr_auc = average_precision_score(
    y_true,
    y_probability
)

baseline = y_true.mean()

plt.figure(figsize=(8, 6))

plt.plot(
    recall,
    precision,
    label=f"Random Forest (AP = {pr_auc:.3f})"
)

plt.axhline(
    baseline,
    linestyle="--",
    label=f"Baseline prevalence ({baseline:.3f})"
)

plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("2024 Out-of-Sample Precision-Recall Curve")
plt.legend()
plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/precision_recall_curve_2024.png",
    dpi=300
)

plt.close()


# ============================================================
# PREDICTED RISK DISTRIBUTION
# ============================================================

plt.figure(figsize=(8, 6))

for actual_class in [0, 1]:

    subset = predictions[
        predictions["distress_12m"] == actual_class
    ]

    plt.hist(
        subset["predicted_probability"],
        bins=10,
        alpha=0.5,
        label=f"Actual distress = {actual_class}"
    )

plt.axvline(
    0.50,
    linestyle="--",
    label="Decision threshold"
)

plt.xlabel("Predicted Distress Probability")
plt.ylabel("Number of Observations")
plt.title("Distribution of 2024 Predicted Distress Risk")
plt.legend()
plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/predicted_risk_distribution_2024.png",
    dpi=300
)

plt.close()


# ============================================================
# ERROR ANALYSIS
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

print("\n--- CLASSIFICATION COUNTS ---")
print(predictions["classification"].value_counts())

print("\n--- FALSE NEGATIVES ---")
print(
    predictions[
        predictions["classification"] == "False Negative"
    ].sort_values(
        "predicted_probability",
        ascending=False
    ).to_string(index=False)
)

print("\n--- FALSE POSITIVES ---")
print(
    predictions[
        predictions["classification"] == "False Positive"
    ].sort_values(
        "predicted_probability",
        ascending=False
    ).to_string(index=False)
)

predictions.to_csv(
    "05_OUTPUTS/final_2024_predictions_analyzed.csv",
    index=False
)

print("\nInterpretation outputs successfully saved.")