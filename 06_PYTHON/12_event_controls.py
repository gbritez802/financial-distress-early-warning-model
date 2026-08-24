import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression


# ============================================================
# LOAD ENHANCED DATASET
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


# ============================================================
# RAW DISTRESS RATES
# ============================================================

print("\n--- RAW HIGH 8-K ACTIVITY COMPARISON ---")

raw = (
    df.groupby("high_8k_activity")
    .agg(
        observations=("distress_12m", "size"),
        distress_events=("distress_12m", "sum"),
        distress_rate=("distress_12m", "mean")
    )
)

print(raw.to_string())


# ============================================================
# COMPANY-LEVEL COMPARISON
# ============================================================

company_rates = (
    df.groupby(
        ["company", "high_8k_activity"]
    )
    .agg(
        observations=("distress_12m", "size"),
        distress_rate=("distress_12m", "mean")
    )
    .reset_index()
)

company_pivot = company_rates.pivot(
    index="company",
    columns="high_8k_activity",
    values="distress_rate"
)

company_pivot.columns = [
    "low_8k_distress_rate",
    "high_8k_distress_rate"
]

company_pivot["difference"] = (
    company_pivot["high_8k_distress_rate"]
    - company_pivot["low_8k_distress_rate"]
)

print("\n--- WITHIN-COMPANY 8-K DIFFERENCES ---")
print(
    company_pivot.sort_values(
        "difference"
    ).to_string()
)

print("\nAverage within-company difference:")
print(
    round(
        company_pivot["difference"].mean(),
        4
    )
)


# ============================================================
# PREPARE FIXED-EFFECT CONTROLS
# ============================================================

event_vars = [
    "high_8k_activity",
    "management_event",
    "restructuring_event",
    "material_agreement_event",
    "acquisition_event"
]

X_events = df[event_vars].copy()

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

X_controlled = pd.concat(
    [
        X_events,
        company_dummies,
        year_dummies
    ],
    axis=1
)

y = df["distress_12m"]


# ============================================================
# LOGISTIC REGRESSION WITH COMPANY + YEAR CONTROLS
# ============================================================

model = LogisticRegression(
    max_iter=5000,
    C=1000,
    solver="lbfgs"
)

model.fit(
    X_controlled,
    y
)

coefficients = pd.Series(
    model.coef_[0],
    index=X_controlled.columns
)

event_results = pd.DataFrame({
    "feature": event_vars,
    "coefficient": coefficients[event_vars]
})

event_results["odds_ratio"] = np.exp(
    event_results["coefficient"]
)

event_results["direction"] = np.where(
    event_results["odds_ratio"] > 1,
    "Higher distress odds",
    "Lower distress odds"
)

print(
    "\n--- EVENT EFFECTS AFTER COMPANY + YEAR CONTROLS ---"
)

print(
    event_results.to_string(
        index=False
    )
)


# ============================================================
# YEAR EFFECTS
# ============================================================

year_results = coefficients[
    coefficients.index.str.startswith("year_")
].sort_values()

print("\n--- YEAR COEFFICIENTS ---")
print(year_results.to_string())