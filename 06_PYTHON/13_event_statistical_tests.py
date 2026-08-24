import pandas as pd
import numpy as np
import statsmodels.api as sm

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(
    "02_CLEAN_DATA/model_dataset_events.csv"
)

print("Dataset:", df.shape)

# ============================================================
# EVENT VARIABLES
# ============================================================

median_8k = df["total_8k_12m"].median()

df["high_8k_activity"] = (
    df["total_8k_12m"] > median_8k
).astype(int)

df["management_event"] = (
    df["management_change_12m"] > 0
).astype(int)

df["restructuring_event"] = (
    df["restructuring_12m"] > 0
).astype(int)

df["material_agreement_event"] = (
    df["material_agreement_12m"] > 0
).astype(int)

df["acquisition_event"] = (
    df["acquisition_disposition_12m"] > 0
).astype(int)

event_vars = [
    "high_8k_activity",
    "management_event",
    "restructuring_event",
    "material_agreement_event",
    "acquisition_event"
]

# ============================================================
# COMPANY + YEAR CONTROLS
# ============================================================

company_dummies = pd.get_dummies(
    df["company"],
    prefix="company",
    drop_first=True,
    dtype=int
)

year_dummies = pd.get_dummies(
    df["year"],
    prefix="year",
    drop_first=True,
    dtype=int
)

X = pd.concat(
    [
        df[event_vars],
        company_dummies,
        year_dummies
    ],
    axis=1
)

X = sm.add_constant(X)

y = df["distress_12m"]

# ============================================================
# LOGISTIC REGRESSION
# ============================================================

model = sm.Logit(
    y,
    X
)

result = model.fit(
    disp=False,
    maxiter=500
)

print("\nModel converged.")

# ============================================================
# EXTRACT EVENT RESULTS
# ============================================================

params = result.params
conf = result.conf_int()
pvalues = result.pvalues

rows = []

for feature in event_vars:

    coefficient = params[feature]

    lower = conf.loc[feature, 0]
    upper = conf.loc[feature, 1]

    rows.append({
        "feature": feature,
        "coefficient": coefficient,
        "odds_ratio": np.exp(coefficient),
        "ci_95_lower": np.exp(lower),
        "ci_95_upper": np.exp(upper),
        "p_value": pvalues[feature]
    })

event_results = pd.DataFrame(rows)

print(
    "\n--- EVENT ODDS RATIOS WITH 95% CONFIDENCE INTERVALS ---"
)

print(
    event_results.to_string(
        index=False
    )
)

# ============================================================
# SIMPLE SIGNIFICANCE FLAG
# ============================================================

event_results["significant_5pct"] = (
    event_results["p_value"] < 0.05
)

print(
    "\n--- SIGNIFICANCE SUMMARY ---"
)

print(
    event_results[
        [
            "feature",
            "odds_ratio",
            "ci_95_lower",
            "ci_95_upper",
            "p_value",
            "significant_5pct"
        ]
    ].to_string(
        index=False
    )
)

# ============================================================
# SAVE RESULTS
# ============================================================

event_results.to_csv(
    "05_OUTPUTS/event_statistical_tests.csv",
    index=False
)

print(
    "\nStatistical test results saved."
)