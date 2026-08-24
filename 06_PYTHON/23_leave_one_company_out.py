import pandas as pd
import numpy as np

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
# DATABASE CONNECTION
# ============================================================

password = getpass("Enter PostgreSQL password: ")

engine = create_engine(
    f"postgresql+psycopg2://postgres:{password}"
    f"@localhost:5432/financial_distress"
)


# ============================================================
# LOAD FINANCIAL DATA
# ============================================================

financial = pd.read_sql(
    """
    SELECT
        cik,
        ticker,
        company,
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
        distress_12m
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
# LOAD VERIFIED STREAK FEATURES
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

print("Merged dataset:", df.shape)
print("Companies:", df["ticker"].nunique())


# ============================================================
# FROZEN FEATURE SET
#
# IMPORTANT:
# Same feature specification used by the frozen final model.
# We are NOT selecting features based on LOCO performance.
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
    "return_on_assets_change_yoy",
    "management_change_12m",
    "restructuring_12m",
    "material_agreement_12m",
    "acquisition_disposition_12m",
    "total_8k_12m",
    "cash_deteriorating_3q",
    "leverage_rising_3q"
]

target = "distress_12m"


# ============================================================
# MODEL FACTORY
#
# Keep hyperparameters frozen.
# ============================================================

def build_model():

    return Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
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
        ]
    )


# ============================================================
# CROSS-COMPANY ROBUSTNESS SAMPLE
#
# IMPORTANT:
#
# We use ONLY observations filed before 2024.
#
# Therefore:
#   - the frozen 2024 holdout remains untouched
#   - this analysis does NOT replace the temporal holdout
#   - this specifically tests transfer across companies
# ============================================================

loco_data = df[
    df["filed"] < pd.Timestamp("2024-01-01")
].copy()

print(
    "\n--- LOCO SAMPLE ---"
)

print(
    "Rows:",
    len(loco_data)
)

print(
    "Companies:",
    loco_data["ticker"].nunique()
)

print(
    "Distress events:",
    int(loco_data[target].sum())
)

print(
    "Distress rate:",
    round(
        loco_data[target].mean(),
        4
    )
)


# ============================================================
# LEAVE ONE COMPANY OUT
# ============================================================

tickers = sorted(
    loco_data["ticker"]
    .dropna()
    .unique()
)

all_predictions = []
company_results = []


for ticker in tickers:

    print(
        "\nHolding out:",
        ticker
    )

    held_out = loco_data[
        loco_data["ticker"] == ticker
    ].copy()

    training = loco_data[
        loco_data["ticker"] != ticker
    ].copy()

    print(
        "Training rows:",
        len(training),
        "| Held-out rows:",
        len(held_out)
    )

    print(
        "Training companies:",
        training["ticker"].nunique()
    )

    # --------------------------------------------------------
    # Sanity checks
    # --------------------------------------------------------

    if ticker in training["ticker"].values:
        raise ValueError(
            f"Leakage detected: {ticker} exists in training."
        )

    if training[target].nunique() < 2:
        raise ValueError(
            f"Training data for {ticker} contains only one class."
        )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    model = build_model()

    model.fit(
        training[features],
        training[target]
    )

    # --------------------------------------------------------
    # Predict completely unseen company
    # --------------------------------------------------------

    probability = model.predict_proba(
        held_out[features]
    )[:, 1]

    prediction = (
        probability >= 0.50
    ).astype(int)

    # --------------------------------------------------------
    # Store row-level predictions
    # --------------------------------------------------------

    temp = held_out[
        [
            "ticker",
            "company",
            "filed",
            "distress_12m"
        ]
    ].copy()

    temp[
        "predicted_probability"
    ] = probability

    temp[
        "predicted_distress"
    ] = prediction

    all_predictions.append(
        temp
    )

    # --------------------------------------------------------
    # Company metrics
    # --------------------------------------------------------

    result = {
        "ticker": ticker,
        "observations": len(held_out),
        "actual_distress": int(
            held_out[target].sum()
        ),
        "predicted_distress": int(
            prediction.sum()
        ),
        "accuracy": accuracy_score(
            held_out[target],
            prediction
        ),
        "precision": precision_score(
            held_out[target],
            prediction,
            zero_division=0
        ),
        "recall": recall_score(
            held_out[target],
            prediction,
            zero_division=0
        ),
        "f1": f1_score(
            held_out[target],
            prediction,
            zero_division=0
        )
    }

    # ROC requires both classes.
    if held_out[target].nunique() == 2:

        result[
            "roc_auc"
        ] = roc_auc_score(
            held_out[target],
            probability
        )

        result[
            "pr_auc"
        ] = average_precision_score(
            held_out[target],
            probability
        )

    else:

        result[
            "roc_auc"
        ] = np.nan

        result[
            "pr_auc"
        ] = np.nan

    company_results.append(
        result
    )


# ============================================================
# COMBINE ALL OUT-OF-COMPANY PREDICTIONS
# ============================================================

predictions = pd.concat(
    all_predictions,
    ignore_index=True
)

results = pd.DataFrame(
    company_results
)


# ============================================================
# OVERALL PERFORMANCE
# ============================================================

overall_roc = roc_auc_score(
    predictions[target],
    predictions["predicted_probability"]
)

overall_pr = average_precision_score(
    predictions[target],
    predictions["predicted_probability"]
)

overall_accuracy = accuracy_score(
    predictions[target],
    predictions["predicted_distress"]
)

overall_precision = precision_score(
    predictions[target],
    predictions["predicted_distress"],
    zero_division=0
)

overall_recall = recall_score(
    predictions[target],
    predictions["predicted_distress"],
    zero_division=0
)

overall_f1 = f1_score(
    predictions[target],
    predictions["predicted_distress"],
    zero_division=0
)

cm = confusion_matrix(
    predictions[target],
    predictions["predicted_distress"]
)


# ============================================================
# RESULTS
# ============================================================

print(
    "\n======================================"
)

print(
    "LEAVE-ONE-COMPANY-OUT ROBUSTNESS"
)

print(
    "======================================"
)

print(
    "Predictions:",
    len(predictions)
)

print(
    "Companies evaluated:",
    predictions["ticker"].nunique()
)

print(
    "ROC-AUC:",
    round(
        overall_roc,
        6
    )
)

print(
    "PR-AUC:",
    round(
        overall_pr,
        6
    )
)

print(
    "Accuracy:",
    round(
        overall_accuracy,
        6
    )
)

print(
    "Precision:",
    round(
        overall_precision,
        6
    )
)

print(
    "Recall:",
    round(
        overall_recall,
        6
    )
)

print(
    "F1:",
    round(
        overall_f1,
        6
    )
)

print(
    "\nConfusion Matrix:"
)

print(cm)


# ============================================================
# COMPANY-LEVEL RESULTS
# ============================================================

print(
    "\n--- COMPANY-LEVEL LOCO RESULTS ---"
)

print(
    results
    .sort_values(
        "roc_auc",
        ascending=False,
        na_position="last"
    )
    .to_string(
        index=False
    )
)


# ============================================================
# SUMMARY OF COMPANY ROC SCORES
# ============================================================

valid_company_roc = (
    results["roc_auc"]
    .dropna()
)

valid_company_pr = (
    results["pr_auc"]
    .dropna()
)

print(
    "\n--- COMPANY METRIC SUMMARY ---"
)

print(
    "Companies with calculable ROC-AUC:",
    len(valid_company_roc)
)

print(
    "Median company ROC-AUC:",
    round(
        valid_company_roc.median(),
        6
    )
)

print(
    "Mean company ROC-AUC:",
    round(
        valid_company_roc.mean(),
        6
    )
)

print(
    "Median company PR-AUC:",
    round(
        valid_company_pr.median(),
        6
    )
)

print(
    "Mean company PR-AUC:",
    round(
        valid_company_pr.mean(),
        6
    )
)


# ============================================================
# SAVE
# ============================================================

predictions.to_csv(
    "05_OUTPUTS/loco_predictions.csv",
    index=False
)

results.to_csv(
    "05_OUTPUTS/loco_company_results.csv",
    index=False
)

print(
    "\nCorrected LOCO predictions saved."
)

print(
    "Corrected LOCO company results saved."
)