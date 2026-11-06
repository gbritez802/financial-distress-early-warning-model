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
# LOAD DATA
# ============================================================

password = getpass("Enter PostgreSQL password: ")

engine = create_engine(
    f"postgresql+psycopg2://postgres:{password}@localhost:5432/financial_distress"
)

df = pd.read_sql(
    """
    SELECT *
    FROM public.model_ready
    ORDER BY filed;
    """,
    engine
)

print("Dataset loaded:", df.shape)


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
# CHRONOLOGICAL SPLITS
# ============================================================

train = df[df["dataset_split"] == "train"].copy()
validation = df[df["dataset_split"] == "validation"].copy()

X_train = train[features]
y_train = train[target]

X_validation = validation[features]
y_validation = validation[target]


# ============================================================
# RANDOM FOREST
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

model.fit(X_train, y_train)


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

probability = model.predict_proba(X_validation)[:, 1]
prediction = (probability >= 0.50).astype(int)


# ============================================================
# METRICS
# ============================================================

print("\n--- RANDOM FOREST VALIDATION ---")

print(
    "ROC-AUC:",
    round(roc_auc_score(y_validation, probability), 3)
)

print(
    "PR-AUC:",
    round(average_precision_score(y_validation, probability), 3)
)

print(
    "Accuracy:",
    round(accuracy_score(y_validation, prediction), 3)
)

print(
    "Precision:",
    round(precision_score(
        y_validation,
        prediction,
        zero_division=0
    ), 3)
)

print(
    "Recall:",
    round(recall_score(
        y_validation,
        prediction,
        zero_division=0
    ), 3)
)

print(
    "F1:",
    round(f1_score(
        y_validation,
        prediction,
        zero_division=0
    ), 3)
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_validation, prediction))


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

forest = model.named_steps["classifier"]

importance = pd.DataFrame({
    "feature": features,
    "importance": forest.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\n--- FEATURE IMPORTANCE ---")
print(importance.to_string(index=False))