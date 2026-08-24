import pandas as pd
import joblib

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

df["filed"] = pd.to_datetime(df["filed"])

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
# DEVELOPMENT AND FINAL TEST SETS
# ============================================================

development = df[
    df["dataset_split"].isin(["train", "validation"])
].copy()

test = df[
    df["dataset_split"] == "test"
].copy()

X_development = development[features]
y_development = development[target]

X_test = test[features]
y_test = test[target]

print("Development observations:", len(development))
print("Test observations:", len(test))

# ============================================================
# LOCKED FINAL MODEL
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

final_model.fit(
    X_development,
    y_development
)

# Locked during validation
threshold = 0.50

# ============================================================
# FINAL 2024 TEST
# ============================================================

test_probability = final_model.predict_proba(
    X_test
)[:, 1]

test_prediction = (
    test_probability >= threshold
).astype(int)

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

print("\n--- FINAL 2024 OUT-OF-SAMPLE TEST ---")
print("Threshold:", threshold)
print("ROC-AUC:", round(roc_auc, 3))
print("PR-AUC:", round(pr_auc, 3))
print("Accuracy:", round(accuracy, 3))
print("Precision:", round(precision, 3))
print("Recall:", round(recall, 3))
print("F1:", round(f1, 3))

print("\nConfusion Matrix:")
print(cm)

# ============================================================
# SAVE INDIVIDUAL TEST PREDICTIONS
# ============================================================

predictions = test[
    [
        "filed",
        "year",
        "distress_12m",
        "future_drawdown_12m"
    ]
].copy()

predictions["predicted_probability"] = test_probability
predictions["predicted_distress"] = test_prediction

predictions.to_csv(
    "05_OUTPUTS/final_2024_predictions.csv",
    index=False
)

# ============================================================
# SAVE FINAL MODEL
# ============================================================

joblib.dump(
    final_model,
    "05_OUTPUTS/final_random_forest_model.joblib"
)

print("\nFinal predictions saved.")
print("Final model saved.")