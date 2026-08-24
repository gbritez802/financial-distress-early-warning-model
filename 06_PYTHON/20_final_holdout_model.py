import pandas as pd
import numpy as np
import joblib
import pandas_market_calendars as mcal

from sqlalchemy import create_engine
from getpass import getpass

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


# ============================================================
# LOAD FINANCIAL DATA
# ============================================================

password = getpass("Enter PostgreSQL password: ")

engine = create_engine(
    f"postgresql+psycopg2://postgres:{password}@localhost:5432/financial_distress"
)

financial = pd.read_sql(
    """
    SELECT
        cik,
        ticker,
        company,
        "end",
        filed,
        market_start_date,
        current_ratio,
        liabilities_to_assets,
        return_on_assets,
        operating_margin,
        cash_to_assets,
        revenue_growth_yoy,
        net_income_growth_yoy,
        operating_margin_change_yoy,
        leverage_change_yoy,
        current_ratio_change_yoy,
        cash_to_assets_change_yoy,
        return_on_assets_change_yoy,
        distress_12m,
        future_drawdown_12m,
        CASE
            WHEN filed < DATE '2022-01-01'
                THEN 'train'
            WHEN filed < DATE '2024-01-01'
                THEN 'validation'
            ELSE 'test'
        END AS dataset_split
    FROM public.model_dataset
    WHERE distress_12m IS NOT NULL
    ORDER BY cik, "end", filed;
    """,
    engine
)

financial["end"] = pd.to_datetime(financial["end"])
financial["filed"] = pd.to_datetime(financial["filed"])
financial["market_start_date"] = pd.to_datetime(
    financial["market_start_date"]
)


# ============================================================
# LOAD EVENT FEATURES
# ============================================================

events = pd.read_csv(
    "02_CLEAN_DATA/model_dataset_events.csv"
)

events["end"] = pd.to_datetime(events["end"])
events["filed"] = pd.to_datetime(events["filed"])

events = events[
    [
        "cik",
        "end",
        "filed",
        "management_change_12m",
        "restructuring_12m",
        "material_agreement_12m",
        "acquisition_disposition_12m",
        "total_8k_12m"
    ]
]


# ============================================================
# LOAD VERIFIED STREAK FEATURES
# ============================================================

streaks = pd.read_csv(
    "02_CLEAN_DATA/financial_deterioration_streaks.csv"
)

streaks["end"] = pd.to_datetime(streaks["end"])
streaks["filed"] = pd.to_datetime(streaks["filed"])

streaks = streaks[
    [
        "cik",
        "end",
        "filed",
        "cash_deteriorating_3q",
        "leverage_rising_3q"
    ]
]


# ============================================================
# MERGE
# ============================================================

df = financial.merge(
    events,
    on=["cik", "end", "filed"],
    how="left",
    validate="one_to_one"
)

df = df.merge(
    streaks,
    on=["cik", "end", "filed"],
    how="left",
    validate="one_to_one"
)

print("Merged dataset:", df.shape)


# ============================================================
# EXACT 252-TRADING-DAY LABEL END
# ============================================================

nyse = mcal.get_calendar("NYSE")

calendar = nyse.schedule(
    start_date=df["market_start_date"].min(),
    end_date=df["market_start_date"].max()
    + pd.Timedelta(days=450)
)

trading_days = pd.DatetimeIndex(
    calendar.index
).tz_localize(None)


def get_label_end(start_date):

    available_days = trading_days[
        trading_days >= start_date
    ]

    if len(available_days) < 252:
        return pd.NaT

    return available_days[251]


df["label_end_date"] = df[
    "market_start_date"
].apply(get_label_end)


# ============================================================
# FROZEN FEATURE SET
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
    "return_on_assets_change_yoy",
    "management_change_12m",
    "restructuring_12m",
    "material_agreement_12m",
    "acquisition_disposition_12m",
    "total_8k_12m",
    "cash_deteriorating_3q",
    "leverage_rising_3q"
]

target = "distress_12m"


# ============================================================
# PURGED DEVELOPMENT + 2024 TEST
# ============================================================

test_start = df.loc[
    df["dataset_split"] == "test",
    "filed"
].min()

development = df[
    (
        df["dataset_split"].isin(
            ["train", "validation"]
        )
    ) &
    (df["label_end_date"] < test_start)
].copy()

test = df[
    df["dataset_split"] == "test"
].copy()

print("\n--- FINAL SAMPLE COUNTS ---")
print("Development:", len(development))
print("Test:", len(test))


# ============================================================
# FINAL FROZEN MODEL
# ============================================================

final_model = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),
    (
        "classifier",
        RandomForestClassifier(
            n_estimators=500,
            max_depth=5,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
    )
])

X_development = development[features]
y_development = development[target]

X_test = test[features]
y_test = test[target]

final_model.fit(
    X_development,
    y_development
)

test_probability = final_model.predict_proba(
    X_test
)[:, 1]

threshold = 0.50

test_prediction = (
    test_probability >= threshold
).astype(int)


# ============================================================
# FINAL METRICS
# ============================================================

roc_auc = roc_auc_score(
    y_test,
    test_probability
)

pr_auc = average_precision_score(
    y_test,
    test_probability
)

accuracy = accuracy_score(
    y_test,
    test_prediction
)

precision = precision_score(
    y_test,
    test_prediction,
    zero_division=0
)

recall = recall_score(
    y_test,
    test_prediction,
    zero_division=0
)

f1 = f1_score(
    y_test,
    test_prediction,
    zero_division=0
)

cm = confusion_matrix(
    y_test,
    test_prediction
)

print("\n--- FINAL FROZEN 2024 HOLDOUT ---")
print("Threshold:", threshold)
print("ROC-AUC:", round(roc_auc, 6))
print("PR-AUC:", round(pr_auc, 6))
print("Accuracy:", round(accuracy, 6))
print("Precision:", round(precision, 6))
print("Recall:", round(recall, 6))
print("F1:", round(f1, 6))

print("\nConfusion Matrix:")
print(cm)


# ============================================================
# BOOTSTRAP 95% CONFIDENCE INTERVALS
# ============================================================

rng = np.random.default_rng(42)

n_bootstrap = 5000

roc_samples = []
pr_samples = []

y_array = np.asarray(y_test)
p_array = np.asarray(test_probability)

n = len(y_array)

for _ in range(n_bootstrap):

    sample_indices = rng.integers(
        0,
        n,
        size=n
    )

    y_sample = y_array[
        sample_indices
    ]

    p_sample = p_array[
        sample_indices
    ]

    # ROC-AUC requires both classes
    if len(np.unique(y_sample)) < 2:
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

roc_lower, roc_upper = np.percentile(
    roc_samples,
    [2.5, 97.5]
)

pr_lower, pr_upper = np.percentile(
    pr_samples,
    [2.5, 97.5]
)

print("\n--- BOOTSTRAP 95% CONFIDENCE INTERVALS ---")

print(
    "ROC-AUC:",
    round(roc_auc, 3),
    "95% CI [",
    round(roc_lower, 3),
    ",",
    round(roc_upper, 3),
    "]"
)

print(
    "PR-AUC:",
    round(pr_auc, 3),
    "95% CI [",
    round(pr_lower, 3),
    ",",
    round(pr_upper, 3),
    "]"
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

forest = final_model.named_steps[
    "classifier"
]

importance = pd.DataFrame({
    "feature": features,
    "importance": forest.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\n--- FINAL FEATURE IMPORTANCE ---")

print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# SAVE TEST PREDICTIONS
# ============================================================

predictions = test[
    [
        "cik",
        "ticker",
        "company",
        "end",
        "filed",
        "distress_12m",
        "future_drawdown_12m"
    ]
].copy()

predictions[
    "predicted_probability"
] = test_probability

predictions[
    "predicted_distress"
] = test_prediction

predictions.to_csv(
    "05_OUTPUTS/final_frozen_2024_predictions.csv",
    index=False
)


# ============================================================
# SAVE FINAL MODEL
# ============================================================

joblib.dump(
    final_model,
    "05_OUTPUTS/final_frozen_random_forest.joblib"
)

importance.to_csv(
    "05_OUTPUTS/final_frozen_feature_importance.csv",
    index=False
)

print("\nFinal frozen predictions saved.")
print("Final frozen model saved.")
print("Final feature importance saved.")