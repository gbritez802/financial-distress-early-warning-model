import pandas as pd

from sqlalchemy import create_engine
from getpass import getpass

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


# ============================================================
# LOAD EVENT FEATURES
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


# ============================================================
# MERGE
# ============================================================

df = financial.merge(
    events,
    on=["cik", "end", "filed"],
    how="left",
    validate="one_to_one"
)

print("Dataset:", df.shape)


# ============================================================
# CREATE FINANCIAL DETERIORATION FLAGS
# ============================================================
df["cash_deteriorating"] = pd.Series(
    pd.NA,
    index=df.index,
    dtype="Int64"
)

df.loc[
    df["cash_to_assets_change_yoy"].notna(),
    "cash_deteriorating"
] = (
    df.loc[
        df["cash_to_assets_change_yoy"].notna(),
        "cash_to_assets_change_yoy"
    ] < 0
).astype(int)


df["leverage_rising"] = pd.Series(
    pd.NA,
    index=df.index,
    dtype="Int64"
)

df.loc[
    df["leverage_change_yoy"].notna(),
    "leverage_rising"
] = (
    df.loc[
        df["leverage_change_yoy"].notna(),
        "leverage_change_yoy"
    ] > 0
).astype(int)


df["roa_deteriorating"] = pd.Series(
    pd.NA,
    index=df.index,
    dtype="Int64"
)

df.loc[
    df["return_on_assets_change_yoy"].notna(),
    "roa_deteriorating"
] = (
    df.loc[
        df["return_on_assets_change_yoy"].notna(),
        "return_on_assets_change_yoy"
    ] < 0
).astype(int)


df["margin_deteriorating"] = pd.Series(
    pd.NA,
    index=df.index,
    dtype="Int64"
)

df.loc[
    df["operating_margin_change_yoy"].notna(),
    "margin_deteriorating"
] = (
    df.loc[
        df["operating_margin_change_yoy"].notna(),
        "operating_margin_change_yoy"
    ] < 0
).astype(int)


df["revenue_declining"] = pd.Series(
    pd.NA,
    index=df.index,
    dtype="Int64"
)

df.loc[
    df["revenue_growth_yoy"].notna(),
    "revenue_declining"
] = (
    df.loc[
        df["revenue_growth_yoy"].notna(),
        "revenue_growth_yoy"
    ] < 0
).astype(int)


# ============================================================
# HIGH 8-K ACTIVITY
# ============================================================

median_8k = df["total_8k_12m"].median()

df["high_8k_activity"] = (
    df["total_8k_12m"] > median_8k
).astype(int)

print(
    "\nMedian 12-month 8-K count:",
    median_8k
)


# ============================================================
# INTERACTION ANALYSIS
# ============================================================

signals = [
    "cash_deteriorating",
    "leverage_rising",
    "roa_deteriorating",
    "margin_deteriorating",
    "revenue_declining"
]

print(
    "\n--- FINANCIAL DETERIORATION × 8-K ACTIVITY ---"
)

for signal in signals:

    temp = (
        df
        .groupby(
            [signal, "high_8k_activity"]
        )
        .agg(
            observations=("distress_12m", "size"),
            distress_events=("distress_12m", "sum"),
            distress_rate=("distress_12m", "mean")
        )
        .reset_index()
    )

    print(
        f"\n{signal.upper()}"
    )

    print(
        temp[
            [
                signal,
                "high_8k_activity",
                "observations",
                "distress_events",
                "distress_rate"
            ]
        ].to_string(index=False)
    )


# ============================================================
# INDIVIDUAL EVENT TYPES
# ============================================================

event_signals = [
    "management_change_12m",
    "restructuring_12m",
    "material_agreement_12m",
    "acquisition_disposition_12m"
]

print(
    "\n--- DISTRESS RATE WITH/WITHOUT EVENT ---"
)

for event in event_signals:

    temp = df.copy()

    temp["event_present"] = (
        temp[event] > 0
    ).astype(int)

    summary = (
        temp
        .groupby("event_present")
        .agg(
            observations=("distress_12m", "size"),
            distress_events=("distress_12m", "sum"),
            distress_rate=("distress_12m", "mean")
        )
    )

    print(
        f"\n{event.upper()}"
    )

    print(
        summary.to_string()
    )