import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

from sklearn.metrics import (
    roc_curve,
    precision_recall_curve,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)

# ============================================================
# LOAD FINAL MODEL OUTPUTS
# ============================================================

predictions = pd.read_csv(
    "05_OUTPUTS/final_frozen_2024_predictions.csv"
)

importance = pd.read_csv(
    "05_OUTPUTS/final_frozen_feature_importance.csv"
)

bootstrap = pd.read_csv(
    "05_OUTPUTS/company_clustered_bootstrap.csv"
)

print("Predictions:", predictions.shape)
print("Importance:", importance.shape)
print("Bootstrap:", bootstrap.shape)

# ============================================================
# BASIC ARRAYS
# ============================================================

y_true = predictions["distress_12m"].to_numpy()

y_prob = predictions[
    "predicted_probability"
].to_numpy()

y_pred = predictions[
    "predicted_distress"
].to_numpy()

roc_auc = roc_auc_score(
    y_true,
    y_prob
)

pr_auc = average_precision_score(
    y_true,
    y_prob
)

# ============================================================
# 1. ROC CURVE
# ============================================================

fpr, tpr, _ = roc_curve(
    y_true,
    y_prob
)

plt.figure(figsize=(8, 6))

plt.plot(
    fpr,
    tpr,
    linewidth=2,
    label=f"Final model (AUC = {roc_auc:.3f})"
)

plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    label="Random"
)

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("2024 Holdout ROC Curve")
plt.legend()
plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/final_roc_curve.png",
    dpi=300
)

plt.close()

# ============================================================
# 2. PRECISION-RECALL CURVE
# ============================================================

precision, recall, _ = precision_recall_curve(
    y_true,
    y_prob
)

baseline_rate = y_true.mean()

plt.figure(figsize=(8, 6))

plt.plot(
    recall,
    precision,
    linewidth=2,
    label=f"Final model (PR-AUC = {pr_auc:.3f})"
)

plt.axhline(
    baseline_rate,
    linestyle="--",
    label=f"Class prevalence = {baseline_rate:.3f}"
)

plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("2024 Holdout Precision-Recall Curve")
plt.legend()
plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/final_pr_curve.png",
    dpi=300
)

plt.close()

# ============================================================
# 3. FEATURE IMPORTANCE
# ============================================================

top_importance = (
    importance
    .sort_values(
        "importance",
        ascending=True
    )
    .tail(15)
)

plt.figure(figsize=(10, 8))

plt.barh(
    top_importance["feature"],
    top_importance["importance"]
)

plt.xlabel("Random Forest Importance")
plt.ylabel("Feature")
plt.title("Top 15 Final Model Feature Importances")
plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/final_feature_importance.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# 4. CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_true,
    y_pred
)

plt.figure(figsize=(6, 5))

plt.imshow(
    cm
)

plt.xticks(
    [0, 1],
    ["No Distress", "Distress"]
)

plt.yticks(
    [0, 1],
    ["No Distress", "Distress"]
)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("2024 Holdout Confusion Matrix")

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(
            j,
            i,
            cm[i, j],
            ha="center",
            va="center"
        )

plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/final_confusion_matrix.png",
    dpi=300
)

plt.close()

# ============================================================
# 5. COMPANY-CLUSTERED BOOTSTRAP DISTRIBUTION
# ============================================================

plt.figure(figsize=(8, 6))

plt.hist(
    bootstrap["roc_auc"],
    bins=30
)

plt.axvline(
    roc_auc,
    linestyle="--",
    linewidth=2,
    label=f"Observed ROC-AUC = {roc_auc:.3f}"
)

plt.xlabel("ROC-AUC")
plt.ylabel("Bootstrap Frequency")
plt.title("Company-Clustered Bootstrap ROC-AUC Distribution")
plt.legend()
plt.tight_layout()

plt.savefig(
    "05_OUTPUTS/bootstrap_roc_distribution.png",
    dpi=300
)

plt.close()

# ============================================================
# 6. MODEL RESULTS TABLE
# ============================================================

row_ci_roc_lower = 0.514
row_ci_roc_upper = 0.786
row_ci_pr_lower = 0.318
row_ci_pr_upper = 0.697

cluster_ci_roc_lower = bootstrap["roc_auc"].quantile(0.025)
cluster_ci_roc_upper = bootstrap["roc_auc"].quantile(0.975)

cluster_ci_pr_lower = bootstrap["pr_auc"].quantile(0.025)
cluster_ci_pr_upper = bootstrap["pr_auc"].quantile(0.975)

results_table = pd.DataFrame(
    {
        "metric": [
            "ROC-AUC",
            "PR-AUC",
            "Accuracy",
            "Precision",
            "Recall",
            "F1"
        ],
        "value": [
            0.653818,
            0.483789,
            0.625000,
            0.428571,
            0.600000,
            0.500000
        ]
    }
)

results_table.to_csv(
    "05_OUTPUTS/final_results_table.csv",
    index=False
)

# ============================================================
# 7. CONFIDENCE INTERVAL TABLE
# ============================================================

ci_table = pd.DataFrame(
    {
        "metric": [
            "ROC-AUC",
            "PR-AUC"
        ],
        "point_estimate": [
            roc_auc,
            pr_auc
        ],
        "row_bootstrap_lower_95": [
            row_ci_roc_lower,
            row_ci_pr_lower
        ],
        "row_bootstrap_upper_95": [
            row_ci_roc_upper,
            row_ci_pr_upper
        ],
        "company_clustered_lower_95": [
            cluster_ci_roc_lower,
            cluster_ci_pr_lower
        ],
        "company_clustered_upper_95": [
            cluster_ci_roc_upper,
            cluster_ci_pr_upper
        ]
    }
)

ci_table.to_csv(
    "05_OUTPUTS/final_confidence_intervals.csv",
    index=False
)

# ============================================================
# DONE
# ============================================================

print("\nFinal visuals saved:")
print("- final_roc_curve.png")
print("- final_pr_curve.png")
print("- final_feature_importance.png")
print("- final_confusion_matrix.png")
print("- bootstrap_roc_distribution.png")
print("- final_results_table.csv")
print("- final_confidence_intervals.csv")