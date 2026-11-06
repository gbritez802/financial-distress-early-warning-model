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
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# ============================================================
# LOAD ORIGINAL FINANCIAL DATA
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

print("Financial rows:", financial.shape)


# ============================================================
# LOAD EVENT FEATURES
# ============================================================

events = pd.read_csv(
    "02_CLEAN_DATA/model_dataset_events.csv"
)

events["end"] = pd.to_datetime(events["end"])
events["filed"] = pd.to_datetime(events["filed"])

event_columns = [
    "cik",
    "end",
    "filed",
    "management_change_12m",
    "restructuring_12m",
    "material_agreement_12m",
    "acquisition_disposition_12m",
    "total_8k_12m"
]

events = events[event_columns]


# ============================================================
# LOAD DETERIORATION STREAK FEATURES
# ============================================================

streaks = pd.read_csv(
    "02_CLEAN_DATA/financial_deterioration_streaks.csv"
)

streaks["end"] = pd.to_datetime(streaks["end"])
streaks["filed"] = pd.to_datetime(streaks["filed"])

streak_columns = [
    "cik",
    "end",
    "filed",
    "margin_deteriorating_2q",
    "margin_deteriorating_3q",
    "cash_deteriorating_2q",
    "cash_deteriorating_3q",
    "leverage_rising_2q",
    "leverage_rising_3q",
    "deterioration_score_2q",
    "deterioration_score_3q"
]

streaks = streaks[streak_columns]


# ============================================================
# MERGE EVERYTHING
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
# FEATURE SETS
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

streak_features = [
    "margin_deteriorating_2q",
    "margin_deteriorating_3q",
    "cash_deteriorating_2q",
    "cash_deteriorating_3q",
    "leverage_rising_2q",
    "leverage_rising_3q",
    "deterioration_score_2q",
    "deterioration_score_3q"
]

baseline_features = (
    financial_features +
    event_features
)

enhanced_features = (
    baseline_features +
    streak_features
)

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
# MODEL
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


def evaluate(
    name,
    features,
    train_df,
    eval_df
):

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

    results = {
        "model": name,
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

    print(f"\n--- {name.upper()} ---")

    for metric in [
        "roc_auc",
        "pr_auc",
        "accuracy",
        "precision",
        "recall",
        "f1"
    ]:
        print(
            f"{metric}:",
            round(results[metric], 6)
        )

    print("\nConfusion Matrix:")
    print(
        confusion_matrix(
            y_eval,
            prediction
        )
    )

    return results, model


# ============================================================
# PURGED VALIDATION COMPARISON
# ============================================================

print("\n==============================")
print("PURGED VALIDATION")
print("==============================")

base_val, _ = evaluate(
    "Fundamentals + Events",
    baseline_features,
    purged_train,
    purged_validation
)

streak_val, streak_model = evaluate(
    "Fundamentals + Events + Streaks",
    enhanced_features,
    purged_train,
    purged_validation
)

print("\n--- VALIDATION STREAK IMPROVEMENT ---")

print(
    "ROC-AUC change:",
    round(
        streak_val["roc_auc"]
        - base_val["roc_auc"],
        6
    )
)

print(
    "PR-AUC change:",
    round(
        streak_val["pr_auc"]
        - base_val["pr_auc"],
        6
    )
)

print(
    "F1 change:",
    round(
        streak_val["f1"]
        - base_val["f1"],
        6
    )
)


# ============================================================
# PURGED 2024 TEST COMPARISON
# ============================================================

print("\n==============================")
print("PURGED 2024 TEST")
print("==============================")

base_test, _ = evaluate(
    "Fundamentals + Events",
    baseline_features,
    purged_development,
    test
)

streak_test, final_streak_model = evaluate(
    "Fundamentals + Events + Streaks",
    enhanced_features,
    purged_development,
    test
)

print("\n--- TEST STREAK IMPROVEMENT ---")

print(
    "ROC-AUC change:",
    round(
        streak_test["roc_auc"]
        - base_test["roc_auc"],
        6
    )
)

print(
    "PR-AUC change:",
    round(
        streak_test["pr_auc"]
        - base_test["pr_auc"],
        6
    )
)

print(
    "F1 change:",
    round(
        streak_test["f1"]
        - base_test["f1"],
        6
    )
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

forest = final_streak_model.named_steps[
    "classifier"
]

importance = pd.DataFrame({
    "feature": enhanced_features,
    "importance": forest.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\n--- FINAL ENHANCED FEATURE IMPORTANCE ---")

print(
    importance.to_string(
        index=False
    )
)