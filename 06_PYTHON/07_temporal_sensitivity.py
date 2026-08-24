import pandas as pd
import numpy as np
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
# LOAD DATA
# ============================================================

password = getpass("Enter PostgreSQL password: ")

engine = create_engine(
    f"postgresql+psycopg2://postgres:{password}@localhost:5432/financial_distress"
)

query = """
SELECT
    ms.*,
    md.market_start_date
FROM public.model_split ms
LEFT JOIN (
    SELECT
        cik,
        filed,
        MIN(market_start_date) AS market_start_date
    FROM public.model_dataset
    GROUP BY cik, filed
) md
    ON ms.cik = md.cik
   AND ms.filed = md.filed
ORDER BY ms.filed;
"""

df = pd.read_sql(query, engine)

df["filed"] = pd.to_datetime(df["filed"])
df["market_start_date"] = pd.to_datetime(df["market_start_date"])

print("Dataset loaded:", df.shape)


# ============================================================
# CALCULATE EXACT 252-TRADING-DAY LABEL END
# ============================================================

nyse = mcal.get_calendar("NYSE")

calendar = nyse.schedule(
    start_date=df["market_start_date"].min(),
    end_date=df["market_start_date"].max() + pd.Timedelta(days=450)
)

trading_days = pd.DatetimeIndex(calendar.index).tz_localize(None)

def get_label_end(start_date):

    available_days = trading_days[
        trading_days >= start_date
    ]

    if len(available_days) < 252:
        return pd.NaT

    # Original R target used the first 252 trading days
    # beginning on/after market_start_date.
    return available_days[251]

df["label_end_date"] = df["market_start_date"].apply(
    get_label_end
)


# ============================================================
# FEATURES AND TARGET
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

target = "distress_12m"


# ============================================================
# SPLIT BOUNDARIES
# ============================================================

validation_start = df.loc[
    df["dataset_split"] == "validation",
    "filed"
].min()

test_start = df.loc[
    df["dataset_split"] == "test",
    "filed"
].min()

print("\nValidation begins:", validation_start.date())
print("Test begins:", test_start.date())


# ============================================================
# PURGED VALIDATION EXPERIMENT
# ============================================================

# Training observations are allowed only if their entire
# 252-session target window ends before validation begins.
purged_train = df[
    (df["dataset_split"] == "train") &
    (df["label_end_date"] < validation_start)
].copy()

# For model selection, validation observations are allowed only
# if their entire target window ends before the final test begins.
purged_validation = df[
    (df["dataset_split"] == "validation") &
    (df["label_end_date"] < test_start)
].copy()

print("\n--- PURGED DEVELOPMENT COUNTS ---")
print("Original train:",
      (df["dataset_split"] == "train").sum())
print("Purged train:",
      len(purged_train))

print("Original validation:",
      (df["dataset_split"] == "validation").sum())
print("Purged validation:",
      len(purged_validation))


# ============================================================
# LOCKED RANDOM FOREST
# ============================================================

model = Pipeline([
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

X_train = purged_train[features]
y_train = purged_train[target]

X_validation = purged_validation[features]
y_validation = purged_validation[target]

model.fit(X_train, y_train)

validation_probability = model.predict_proba(
    X_validation
)[:, 1]

validation_prediction = (
    validation_probability >= 0.50
).astype(int)

print("\n--- PURGED VALIDATION RESULTS ---")

print(
    "ROC-AUC:",
    round(
        roc_auc_score(
            y_validation,
            validation_probability
        ),
        3
    )
)

print(
    "PR-AUC:",
    round(
        average_precision_score(
            y_validation,
            validation_probability
        ),
        3
    )
)

print(
    "Accuracy:",
    round(
        accuracy_score(
            y_validation,
            validation_prediction
        ),
        3
    )
)

print(
    "Precision:",
    round(
        precision_score(
            y_validation,
            validation_prediction,
            zero_division=0
        ),
        3
    )
)

print(
    "Recall:",
    round(
        recall_score(
            y_validation,
            validation_prediction,
            zero_division=0
        ),
        3
    )
)

print(
    "F1:",
    round(
        f1_score(
            y_validation,
            validation_prediction,
            zero_division=0
        ),
        3
    )
)

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_validation,
        validation_prediction
    )
)


# ============================================================
# STRICT FINAL TEST SENSITIVITY
# ============================================================

# Development observations may be used only if their entire
# target window ends BEFORE 2024 test observations begin.
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

print("\n--- STRICT FINAL DEVELOPMENT COUNTS ---")
print(
    "Original development:",
    df["dataset_split"].isin(
        ["train", "validation"]
    ).sum()
)
print(
    "Purged development:",
    len(purged_development)
)
print(
    "Test:",
    len(test)
)

X_development = purged_development[features]
y_development = purged_development[target]

X_test = test[features]
y_test = test[target]

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

final_model.fit(
    X_development,
    y_development
)

test_probability = final_model.predict_proba(
    X_test
)[:, 1]

test_prediction = (
    test_probability >= 0.50
).astype(int)

print("\n--- PURGED 2024 OUT-OF-SAMPLE TEST ---")

print(
    "ROC-AUC:",
    round(
        roc_auc_score(
            y_test,
            test_probability
        ),
        3
    )
)

print(
    "PR-AUC:",
    round(
        average_precision_score(
            y_test,
            test_probability
        ),
        3
    )
)

print(
    "Accuracy:",
    round(
        accuracy_score(
            y_test,
            test_prediction
        ),
        3
    )
)

print(
    "Precision:",
    round(
        precision_score(
            y_test,
            test_prediction,
            zero_division=0
        ),
        3
    )
)

print(
    "Recall:",
    round(
        recall_score(
            y_test,
            test_prediction,
            zero_division=0
        ),
        3
    )
)

print(
    "F1:",
    round(
        f1_score(
            y_test,
            test_prediction,
            zero_division=0
        ),
        3
    )
)

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_test,
        test_prediction
    )
)