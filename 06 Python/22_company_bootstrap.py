import pandas as pd
import numpy as np

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score
)

# ============================================================
# LOAD FINAL FROZEN 2024 PREDICTIONS
# ============================================================

predictions = pd.read_csv(
    "05_OUTPUTS/final_frozen_2024_predictions.csv"
)

print("Predictions loaded:", predictions.shape)

required_columns = [
    "ticker",
    "distress_12m",
    "predicted_probability"
]

missing = [
    col for col in required_columns
    if col not in predictions.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

print(
    "Companies:",
    predictions["ticker"].nunique()
)


# ============================================================
# ORIGINAL HOLDOUT PERFORMANCE
# ============================================================

y_true = predictions["distress_12m"].to_numpy()
y_prob = predictions[
    "predicted_probability"
].to_numpy()

original_roc = roc_auc_score(
    y_true,
    y_prob
)

original_pr = average_precision_score(
    y_true,
    y_prob
)

print("\n--- ORIGINAL 2024 HOLDOUT ---")
print(
    "ROC-AUC:",
    round(original_roc, 6)
)

print(
    "PR-AUC:",
    round(original_pr, 6)
)


# ============================================================
# COMPANY-CLUSTERED BOOTSTRAP
#
# Resample whole companies instead of individual observations.
# If a ticker is selected, all of its 2024 observations move
# together into the bootstrap sample.
# ============================================================

rng = np.random.default_rng(42)

tickers = predictions[
    "ticker"
].drop_duplicates().to_numpy()

n_companies = len(tickers)

n_bootstrap = 5000

roc_samples = []
pr_samples = []

skipped_single_class = 0

for _ in range(n_bootstrap):

    sampled_tickers = rng.choice(
        tickers,
        size=n_companies,
        replace=True
    )

    sample_parts = []

    # Keep duplicates when a company is sampled more than once.
    for ticker in sampled_tickers:

        company_rows = predictions[
            predictions["ticker"] == ticker
        ].copy()

        sample_parts.append(
            company_rows
        )

    sample = pd.concat(
        sample_parts,
        ignore_index=True
    )

    y_sample = sample[
        "distress_12m"
    ].to_numpy()

    p_sample = sample[
        "predicted_probability"
    ].to_numpy()

    # ROC-AUC cannot be calculated if the sample contains
    # only one target class.
    if len(np.unique(y_sample)) < 2:

        skipped_single_class += 1
        continue

    roc_samples.append(
        roc_auc_score(
            y_sample,
            p_sample
        )
    )

    pr_samples.append(
        average_precision_score(
            y_sample,
            p_sample
        )
    )


# ============================================================
# CONFIDENCE INTERVALS
# ============================================================

roc_samples = np.asarray(
    roc_samples
)

pr_samples = np.asarray(
    pr_samples
)

roc_lower, roc_upper = np.percentile(
    roc_samples,
    [2.5, 97.5]
)

pr_lower, pr_upper = np.percentile(
    pr_samples,
    [2.5, 97.5]
)


print(
    "\n--- COMPANY-CLUSTERED BOOTSTRAP 95% CI ---"
)

print(
    "Successful bootstrap samples:",
    len(roc_samples)
)

print(
    "Skipped single-class samples:",
    skipped_single_class
)

print(
    "\nROC-AUC:",
    round(original_roc, 3),
    "95% CI [",
    round(roc_lower, 3),
    ",",
    round(roc_upper, 3),
    "]"
)

print(
    "PR-AUC:",
    round(original_pr, 3),
    "95% CI [",
    round(pr_lower, 3),
    ",",
    round(pr_upper, 3),
    "]"
)


# ============================================================
# BOOTSTRAP DISTRIBUTION SUMMARY
# ============================================================

print(
    "\n--- BOOTSTRAP DISTRIBUTION SUMMARY ---"
)

print(
    "ROC mean:",
    round(
        roc_samples.mean(),
        3
    )
)

print(
    "ROC median:",
    round(
        np.median(roc_samples),
        3
    )
)

print(
    "ROC std:",
    round(
        roc_samples.std(),
        3
    )
)

print(
    "PR mean:",
    round(
        pr_samples.mean(),
        3
    )
)

print(
    "PR median:",
    round(
        np.median(pr_samples),
        3
    )
)

print(
    "PR std:",
    round(
        pr_samples.std(),
        3
    )
)


# ============================================================
# SAVE BOOTSTRAP RESULTS
# ============================================================

bootstrap_results = pd.DataFrame({
    "roc_auc": roc_samples,
    "pr_auc": pr_samples
})

bootstrap_results.to_csv(
    "05_OUTPUTS/company_clustered_bootstrap.csv",
    index=False
)

print(
    "\nCompany-clustered bootstrap results saved."
)