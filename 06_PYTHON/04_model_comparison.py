import pandas as pd
import numpy as np

from sqlalchemy import create_engine
from getpass import getpass

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
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

train = df[df["dataset_split"] == "train"].copy()
validation = df[df["dataset_split"] == "validation"].copy()

X_train = train[features]
y_train = train[target]

X_validation = validation[features]
y_validation = validation[target]

# ============================================================
# MODELS
# ============================================================

logistic = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
    (
        "classifier",
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        )
    )
])

random_forest = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
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

models = {
    "Logistic Regression": logistic,
    "Random Forest": random_forest
}

# ============================================================
# THRESHOLD COMPARISON
# ============================================================

thresholds = np.arange(0.20, 0.81, 0.05)

all_results = []

for model_name, model in models.items():

    model.fit(X_train, y_train)

    probability = model.predict_proba(X_validation)[:, 1]

    roc_auc = roc_auc_score(
        y_validation,
        probability
    )

    pr_auc = average_precision_score(
        y_validation,
        probability
    )

    for threshold in thresholds:

        prediction = (
            probability >= threshold
        ).astype(int)

        precision = precision_score(
            y_validation,
            prediction,
            zero_division=0
        )

        recall = recall_score(
            y_validation,
            prediction,
            zero_division=0
        )

        f1 = f1_score(
            y_validation,
            prediction,
            zero_division=0
        )

        accuracy = accuracy_score(
            y_validation,
            prediction
        )

        all_results.append({
            "model": model_name,
            "threshold": round(float(threshold), 2),
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        })

results = pd.DataFrame(all_results)

# ============================================================
# FILTER TO PRACTICAL THRESHOLDS
# ============================================================

practical = results[
    results["recall"] >= 0.60
].copy()

practical = practical.sort_values(
    ["f1", "pr_auc", "roc_auc"],
    ascending=False
)

print("\n--- ALL PRACTICAL THRESHOLDS ---")
print(
    practical[
        [
            "model",
            "threshold",
            "roc_auc",
            "pr_auc",
            "accuracy",
            "precision",
            "recall",
            "f1"
        ]
    ].to_string(index=False)
)

# ============================================================
# BEST VALIDATION CONFIGURATION
# ============================================================

best = practical.iloc[0]

print("\n--- BEST VALIDATION CONFIGURATION ---")
print(best)

best_model_name = best["model"]
best_threshold = best["threshold"]

best_model = models[best_model_name]

best_model.fit(X_train, y_train)

best_probability = best_model.predict_proba(
    X_validation
)[:, 1]

best_prediction = (
    best_probability >= best_threshold
).astype(int)

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_validation,
        best_prediction
    )
)