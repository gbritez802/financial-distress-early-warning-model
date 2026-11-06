import pandas as pd
import numpy as np

from sqlalchemy import create_engine
from getpass import getpass

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
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
SELECT *
FROM public.model_ready
ORDER BY filed;
"""

df = pd.read_sql(query, engine)

df["filed"] = pd.to_datetime(df["filed"])

print("Dataset loaded:", df.shape)


# ============================================================
# DEFINE FEATURES AND TARGET
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
test = df[df["dataset_split"] == "test"].copy()

X_train = train[features]
y_train = train[target]

X_validation = validation[features]
y_validation = validation[target]

X_test = test[features]
y_test = test[target]

print("\nTrain:", X_train.shape)
print("Validation:", X_validation.shape)
print("Test:", X_test.shape)


# ============================================================
# BASELINE LOGISTIC REGRESSION
# ============================================================

model = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="median")
    ),
    (
        "scaler",
        StandardScaler()
    ),
    (
        "classifier",
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        )
    )
])

model.fit(X_train, y_train)


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

validation_probability = model.predict_proba(X_validation)[:, 1]
validation_prediction = (
    validation_probability >= 0.50
).astype(int)


# ============================================================
# VALIDATION METRICS
# ============================================================

roc_auc = roc_auc_score(
    y_validation,
    validation_probability
)

pr_auc = average_precision_score(
    y_validation,
    validation_probability
)

accuracy = accuracy_score(
    y_validation,
    validation_prediction
)

precision = precision_score(
    y_validation,
    validation_prediction,
    zero_division=0
)

recall = recall_score(
    y_validation,
    validation_prediction,
    zero_division=0
)

f1 = f1_score(
    y_validation,
    validation_prediction,
    zero_division=0
)

cm = confusion_matrix(
    y_validation,
    validation_prediction
)

print("\n--- BASELINE LOGISTIC REGRESSION ---")
print("Validation ROC-AUC:", round(roc_auc, 3))
print("Validation PR-AUC:", round(pr_auc, 3))
print("Validation Accuracy:", round(accuracy, 3))
print("Validation Precision:", round(precision, 3))
print("Validation Recall:", round(recall, 3))
print("Validation F1:", round(f1, 3))

print("\nConfusion Matrix:")
print(cm)