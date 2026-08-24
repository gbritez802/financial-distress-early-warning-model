import pandas as pd

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
# LOAD ENHANCED DATASET
# ============================================================

df = pd.read_csv(
    "02_CLEAN_DATA/model_dataset_events.csv"
)

df["filed"] = pd.to_datetime(df["filed"])

print("Dataset loaded:", df.shape)


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

enhanced_features = (
    financial_features +
    event_features
)

target = "distress_12m"


# ============================================================
# CHRONOLOGICAL SPLITS
# ============================================================

train = df[
    df["filed"] < "2022-01-01"
].copy()

validation = df[
    (df["filed"] >= "2022-01-01") &
    (df["filed"] < "2024-01-01")
].copy()

print("\nTrain observations:", len(train))
print("Validation observations:", len(validation))


# ============================================================
# MODEL FUNCTION
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


def evaluate_model(
    model_name,
    features
):

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
        "model": model_name,
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

    print(
        f"\n--- {model_name.upper()} ---"
    )

    for key, value in results.items():

        if key != "model":
            print(
                f"{key}:",
                round(value, 3)
            )

    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y_validation,
            prediction
        )
    )

    return (
        results,
        model
    )


# ============================================================
# MODEL A: FUNDAMENTALS ONLY
# ============================================================

fundamental_results, fundamental_model = evaluate_model(
    "Fundamentals Only",
    financial_features
)


# ============================================================
# MODEL B: FUNDAMENTALS + EVENTS
# ============================================================

enhanced_results, enhanced_model = evaluate_model(
    "Fundamentals + Events",
    enhanced_features
)


# ============================================================
# COMPARISON TABLE
# ============================================================

comparison = pd.DataFrame([
    fundamental_results,
    enhanced_results
])

print("\n--- MODEL COMPARISON ---")

print(
    comparison[
        [
            "model",
            "roc_auc",
            "pr_auc",
            "accuracy",
            "precision",
            "recall",
            "f1"
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# EVENT FEATURE IMPORTANCE
# ============================================================

forest = enhanced_model.named_steps[
    "classifier"
]

importance = pd.DataFrame({
    "feature": enhanced_features,
    "importance": forest.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\n--- ENHANCED MODEL FEATURE IMPORTANCE ---")

print(
    importance.to_string(
        index=False
    )
)