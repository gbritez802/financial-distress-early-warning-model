import pandas as pd
import pandas_market_calendars as mcal

from sqlalchemy import create_engine
from getpass import getpass

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score
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
# LOAD STREAK FEATURES
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
        "margin_deteriorating_3q",
        "leverage_rising_3q",
        "deterioration_score_3q"
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

print("Merged rows:", df.shape)

# ============================================================
# LABEL END DATES FOR PURGE
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
# BASELINE FEATURES
# ============================================================

financial_features = [
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

event_features = [
    "management_change_12m",
    "restructuring_12m",
    "material_agreement_12m",
    "acquisition_disposition_12m",
    "total_8k_12m"
]

baseline_features = (
    financial_features +
    event_features
)

candidate_streaks = [
    "cash_deteriorating_3q",
    "margin_deteriorating_3q",
    "leverage_rising_3q",
    "deterioration_score_3q"
]

target = "distress_12m"

# ============================================================
# PURGED SPLITS
# ============================================================

validation_start = df.loc[
    df["dataset_split"] == "validation",
    "filed"
].min()

test_start = df.loc[
    df["dataset_split"] == "test",
    "filed"
].min()

purged_train = df[
    (df["dataset_split"] == "train") &
    (df["label_end_date"] < validation_start)
].copy()

purged_validation = df[
    (df["dataset_split"] == "validation") &
    (df["label_end_date"] < test_start)
].copy()

purged_development = df[
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

print("\n--- PURGED COUNTS ---")
print("Train:", len(purged_train))
print("Validation:", len(purged_validation))
print("Development:", len(purged_development))
print("Test:", len(test))

# ============================================================
# MODEL FACTORY
# ============================================================

def build_model():
    return Pipeline([
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

# ============================================================
# EVALUATION FUNCTION
# ============================================================

def evaluate(features, train_df, eval_df):

    X_train = train_df[features]
    y_train = train_df[target]

    X_eval = eval_df[features]
    y_eval = eval_df[target]

    model = build_model()

    model.fit(
        X_train,
        y_train
    )

    probability = model.predict_proba(
        X_eval
    )[:, 1]

    prediction = (
        probability >= 0.50
    ).astype(int)

    return {
        "roc_auc": roc_auc_score(
            y_eval,
            probability
        ),
        "pr_auc": average_precision_score(
            y_eval,
            probability
        ),
        "accuracy": accuracy_score(
            y_eval,
            prediction
        ),
        "precision": precision_score(
            y_eval,
            prediction,
            zero_division=0
        ),
        "recall": recall_score(
            y_eval,
            prediction,
            zero_division=0
        ),
        "f1": f1_score(
            y_eval,
            prediction,
            zero_division=0
        )
    }

# ============================================================
# BASELINE
# ============================================================

baseline_val = evaluate(
    baseline_features,
    purged_train,
    purged_validation
)

baseline_test = evaluate(
    baseline_features,
    purged_development,
    test
)

# ============================================================
# ONE-FEATURE-AT-A-TIME ABLATION
# ============================================================

rows = []

for streak in candidate_streaks:

    features = (
        baseline_features +
        [streak]
    )

    val = evaluate(
        features,
        purged_train,
        purged_validation
    )

    test_result = evaluate(
        features,
        purged_development,
        test
    )

    rows.append({
        "feature_added": streak,

        "val_roc_auc": val["roc_auc"],
        "val_pr_auc": val["pr_auc"],
        "val_f1": val["f1"],

        "test_roc_auc": test_result["roc_auc"],
        "test_pr_auc": test_result["pr_auc"],
        "test_f1": test_result["f1"],

        "test_recall": test_result["recall"],
        "test_precision": test_result["precision"]
    })

results = pd.DataFrame(rows)

# ============================================================
# PRINT BASELINE
# ============================================================

print("\n--- BASELINE ---")

print(
    "Validation ROC-AUC:",
    round(baseline_val["roc_auc"], 6)
)

print(
    "Validation PR-AUC:",
    round(baseline_val["pr_auc"], 6)
)

print(
    "Validation F1:",
    round(baseline_val["f1"], 6)
)

print(
    "Test ROC-AUC:",
    round(baseline_test["roc_auc"], 6)
)

print(
    "Test PR-AUC:",
    round(baseline_test["pr_auc"], 6)
)

print(
    "Test F1:",
    round(baseline_test["f1"], 6)
)

# ============================================================
# PRINT ABLATION RESULTS
# ============================================================

print("\n--- TARGETED STREAK ABLATION ---")

print(
    results.to_string(
        index=False
    )
)

# ============================================================
# CHANGES RELATIVE TO BASELINE
# ============================================================

results["val_pr_change"] = (
    results["val_pr_auc"]
    - baseline_val["pr_auc"]
)

results["val_f1_change"] = (
    results["val_f1"]
    - baseline_val["f1"]
)

results["test_pr_change"] = (
    results["test_pr_auc"]
    - baseline_test["pr_auc"]
)

results["test_f1_change"] = (
    results["test_f1"]
    - baseline_test["f1"]
)

print("\n--- CHANGE VS BASELINE ---")

print(
    results[
        [
            "feature_added",
            "val_pr_change",
            "val_f1_change",
            "test_pr_change",
            "test_f1_change"
        ]
    ].to_string(
        index=False
    )
)