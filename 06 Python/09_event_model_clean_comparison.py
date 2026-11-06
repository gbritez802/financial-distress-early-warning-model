import pandas as pd

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
# LOAD ORIGINAL FINANCIAL DATA FROM POSTGRESQL
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

print("PostgreSQL financial rows:", financial.shape)


# ============================================================
# LOAD EVENT FEATURES FROM R CSV
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

print("Event rows:", events.shape)


# ============================================================
# MERGE ON UNIQUE COMPANY-QUARTER KEY
# ============================================================

df = financial.merge(
    events,
    on=["cik", "end", "filed"],
    how="left",
    validate="one_to_one"
)

print("Merged dataset:", df.shape)

print("\n--- SPLIT COUNTS ---")
print(df["dataset_split"].value_counts())

print("\nMissing event values:")
print(
    df[
        [
            "management_change_12m",
            "restructuring_12m",
            "material_agreement_12m",
            "acquisition_disposition_12m",
            "total_8k_12m"
        ]
    ].isna().sum()
)


# ============================================================
# FEATURES
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

enhanced_features = financial_features + event_features

target = "distress_12m"


# ============================================================
# LOCKED SPLITS
# ============================================================

train = df[
    df["dataset_split"] == "train"
].copy()

validation = df[
    df["dataset_split"] == "validation"
].copy()

print("\nTrain:", len(train))
print("Validation:", len(validation))


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


def evaluate(name, features):

    X_train = train[features]
    y_train = train[target]

    X_validation = validation[features]
    y_validation = validation[target]

    model = build_model()

    model.fit(
        X_train,
        y_train
    )

    probability = model.predict_proba(
        X_validation
    )[:, 1]

    prediction = (
        probability >= 0.50
    ).astype(int)

    results = {
        "model": name,
        "roc_auc": roc_auc_score(
            y_validation,
            probability
        ),
        "pr_auc": average_precision_score(
            y_validation,
            probability
        ),
        "accuracy": accuracy_score(
            y_validation,
            prediction
        ),
        "precision": precision_score(
            y_validation,
            prediction,
            zero_division=0
        ),
        "recall": recall_score(
            y_validation,
            prediction,
            zero_division=0
        ),
        "f1": f1_score(
            y_validation,
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
            y_validation,
            prediction
        )
    )

    return results, model


# ============================================================
# COMPARE
# ============================================================

fundamental_results, fundamental_model = evaluate(
    "Fundamentals Only",
    financial_features
)

enhanced_results, enhanced_model = evaluate(
    "Fundamentals + Events",
    enhanced_features
)

print("\n--- EVENT FEATURE IMPROVEMENT ---")

print(
    "ROC-AUC change:",
    round(
        enhanced_results["roc_auc"]
        - fundamental_results["roc_auc"],
        6
    )
)

print(
    "PR-AUC change:",
    round(
        enhanced_results["pr_auc"]
        - fundamental_results["pr_auc"],
        6
    )
)

print(
    "F1 change:",
    round(
        enhanced_results["f1"]
        - fundamental_results["f1"],
        6
    )
)