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
# LOAD SEC EVENT FEATURES
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
# LOAD VERIFIED QUARTER-STREAK FEATURES
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

print("Merged rows:", df.shape)


# ============================================================
# BUILD EXACT 252-TRADING-DAY LABEL END
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

baseline_features = (
    financial_features +
    event_features
)

candidate_sets = {
    "Baseline":
        baseline_features,

    "Baseline + Cash 3Q":
        baseline_features +
        ["cash_deteriorating_3q"],

    "Baseline + Leverage 3Q":
        baseline_features +
        ["leverage_rising_3q"],

    "Baseline + Cash + Leverage 3Q":
        baseline_features +
        [
            "cash_deteriorating_3q",
            "leverage_rising_3q"
        ]
}

target = "distress_12m"


# ============================================================
# PURGED TRAIN / VALIDATION
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

print("\n--- PURGED COUNTS ---")
print("Train:", len(purged_train))
print("Validation:", len(purged_validation))


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


def evaluate(features):

    X_train = purged_train[features]
    y_train = purged_train[target]

    X_val = purged_validation[features]
    y_val = purged_validation[target]

    model = build_model()

    model.fit(
        X_train,
        y_train
    )

    probability = model.predict_proba(
        X_val
    )[:, 1]

    prediction = (
        probability >= 0.50
    ).astype(int)

    return {
        "roc_auc":
            roc_auc_score(
                y_val,
                probability
            ),

        "pr_auc":
            average_precision_score(
                y_val,
                probability
            ),

        "accuracy":
            accuracy_score(
                y_val,
                prediction
            ),

        "precision":
            precision_score(
                y_val,
                prediction,
                zero_division=0
            ),

        "recall":
            recall_score(
                y_val,
                prediction,
                zero_division=0
            ),

        "f1":
            f1_score(
                y_val,
                prediction,
                zero_division=0
            )
    }


# ============================================================
# RUN CANDIDATE COMPARISON
# ============================================================

rows = []

for name, features in candidate_sets.items():

    result = evaluate(features)

    rows.append({
        "candidate": name,
        **result
    })

results = pd.DataFrame(rows)


# ============================================================
# OUTPUT
# ============================================================

print("\n--- PURGED VALIDATION CANDIDATE COMPARISON ---")

print(
    results.to_string(
        index=False
    )
)


# ============================================================
# RANK CANDIDATES
#
# Primary:
#   PR-AUC
#
# Secondary:
#   F1
#
# Because distress is the minority class.
# ============================================================

ranked = results.sort_values(
    [
        "pr_auc",
        "f1",
        "roc_auc"
    ],
    ascending=False
)

print("\n--- CANDIDATE RANKING ---")

print(
    ranked[
        [
            "candidate",
            "pr_auc",
            "f1",
            "roc_auc",
            "recall",
            "precision"
        ]
    ].to_string(
        index=False
    )
)

winner = ranked.iloc[0]

print("\n--- VALIDATION WINNER ---")

print(
    "Candidate:",
    winner["candidate"]
)

print(
    "PR-AUC:",
    round(winner["pr_auc"], 6)
)

print(
    "F1:",
    round(winner["f1"], 6)
)

print(
    "ROC-AUC:",
    round(winner["roc_auc"], 6)
)