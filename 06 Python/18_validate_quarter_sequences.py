import pandas as pd

from sqlalchemy import create_engine
from getpass import getpass


# ============================================================
# DATABASE CONNECTION
# ============================================================

password = getpass("Enter PostgreSQL password: ")

engine = create_engine(
    f"postgresql+psycopg2://postgres:{password}@localhost:5432/financial_distress"
)


# ============================================================
# LOAD FINANCIAL DATA
# ============================================================

query = """
SELECT *
FROM public.model_dataset
WHERE distress_12m IS NOT NULL
ORDER BY cik, "end", filed;
"""

df = pd.read_sql(query, engine)

df["end"] = pd.to_datetime(df["end"])
df["filed"] = pd.to_datetime(df["filed"])

df = (
    df
    .sort_values(["cik", "end", "filed"])
    .reset_index(drop=True)
)

print("Dataset loaded:", df.shape)


# ============================================================
# CURRENT-PERIOD DETERIORATION FLAGS
# ============================================================

df["margin_deteriorating"] = (
    df["operating_margin_change_yoy"] < 0
).astype(int)

df["roa_deteriorating"] = (
    df["return_on_assets_change_yoy"] < 0
).astype(int)

df["cash_deteriorating"] = (
    df["cash_to_assets_change_yoy"] < 0
).astype(int)

df["leverage_rising"] = (
    df["leverage_change_yoy"] > 0
).astype(int)

df["revenue_deteriorating"] = (
    df["revenue_growth_yoy"] < 0
).astype(int)


# ============================================================
# VALIDATE QUARTER SEQUENCES
# ============================================================

df["previous_end"] = (
    df.groupby("cik")["end"]
    .shift(1)
)

df["days_since_previous"] = (
    df["end"] - df["previous_end"]
).dt.days

# A valid quarter-to-quarter gap is approximately 3 months.
df["valid_quarter_gap"] = (
    df["days_since_previous"]
    .between(75, 105)
)

# Needed to validate a true 3-quarter sequence.
df["previous_gap_valid"] = (
    df.groupby("cik")["valid_quarter_gap"]
    .shift(1)
    .fillna(False)
    .astype(bool)
)


# ============================================================
# TRUE CONSECUTIVE-QUARTER STREAKS
# ============================================================

signals = [
    "margin_deteriorating",
    "roa_deteriorating",
    "cash_deteriorating",
    "leverage_rising",
    "revenue_deteriorating"
]

for signal in signals:

    previous_1 = (
        df.groupby("cik")[signal]
        .shift(1)
    )

    previous_2 = (
        df.groupby("cik")[signal]
        .shift(2)
    )

    # Current quarter + previous quarter
    df[f"{signal}_2q"] = (
        (df[signal] == 1) &
        (previous_1 == 1) &
        df["valid_quarter_gap"]
    ).astype(int)

    # Current quarter + previous TWO quarters
    df[f"{signal}_3q"] = (
        (df[signal] == 1) &
        (previous_1 == 1) &
        (previous_2 == 1) &
        df["valid_quarter_gap"] &
        df["previous_gap_valid"]
    ).astype(int)


# ============================================================
# QUARTER-SEQUENCE VALIDATION SUMMARY
# ============================================================

print("\n--- QUARTER SEQUENCE CHECK ---")

print(
    "Valid quarter gaps:",
    int(df["valid_quarter_gap"].sum())
)

valid_3q_sequence = (
    df["valid_quarter_gap"] &
    df["previous_gap_valid"]
)

print(
    "Valid 3-quarter sequences:",
    int(valid_3q_sequence.sum())
)


# ============================================================
# DETERIORATION STREAK COUNTS
# ============================================================

print("\n--- DETERIORATION STREAK COUNTS ---")

for signal in signals:

    print(f"\n{signal.upper()}")

    print(
        "2-quarter streak:",
        int(df[f"{signal}_2q"].sum())
    )

    print(
        "3-quarter streak:",
        int(df[f"{signal}_3q"].sum())
    )


# ============================================================
# DISTRESS RATES AFTER STREAKS
# ============================================================

print("\n======================================")
print("DISTRESS RATES AFTER DETERIORATION")
print("======================================")

for signal in signals:

    print(f"\n--- {signal.upper()} ---")

    for horizon in ["2q", "3q"]:

        feature = f"{signal}_{horizon}"

        result = (
            df
            .groupby(feature)["distress_12m"]
            .agg(
                observations="count",
                distress_events="sum",
                distress_rate="mean"
            )
        )

        print(f"\n{horizon.upper()} STREAK")

        print(
            result.to_string()
        )


# ============================================================
# COMBINED DETERIORATION SCORES
# ============================================================

streak_2q_features = [
    f"{signal}_2q"
    for signal in signals
]

streak_3q_features = [
    f"{signal}_3q"
    for signal in signals
]

df["deterioration_score_2q"] = (
    df[streak_2q_features]
    .sum(axis=1)
)

df["deterioration_score_3q"] = (
    df[streak_3q_features]
    .sum(axis=1)
)


# ============================================================
# SCORE SUMMARIES
# ============================================================

print("\n--- 2-QUARTER DETERIORATION SCORE ---")

score_2q = (
    df
    .groupby("deterioration_score_2q")["distress_12m"]
    .agg(
        observations="count",
        distress_events="sum",
        distress_rate="mean"
    )
)

print(
    score_2q.to_string()
)


print("\n--- 3-QUARTER DETERIORATION SCORE ---")

score_3q = (
    df
    .groupby("deterioration_score_3q")["distress_12m"]
    .agg(
        observations="count",
        distress_events="sum",
        distress_rate="mean"
    )
)

print(
    score_3q.to_string()
)


# ============================================================
# SAVE CLEAN STREAK DATASET
# ============================================================

df.to_csv(
    "02_CLEAN_DATA/financial_deterioration_streaks.csv",
    index=False
)

print(
    "\nCorrected deterioration streak dataset saved."
)