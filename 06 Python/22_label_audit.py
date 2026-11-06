import pandas as pd
import numpy as np

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
# LOAD MODEL DATA
# ============================================================

model = pd.read_sql(
    """
    SELECT
        cik,
        ticker,
        company,
        "end",
        filed,
        market_start_date,
        distress_12m,
        future_drawdown_12m
    FROM public.model_dataset
    WHERE ticker IN ('AAPL', 'AMZN', 'GOOGL', 'UNH')
    ORDER BY ticker, filed;
    """,
    engine
)

model["filed"] = pd.to_datetime(model["filed"])
model["end"] = pd.to_datetime(model["end"])
model["market_start_date"] = pd.to_datetime(
    model["market_start_date"]
)

print("\n--- MODEL LABELS TO AUDIT ---")
print(
    model[
        [
            "ticker",
            "filed",
            "market_start_date",
            "future_drawdown_12m",
            "distress_12m"
        ]
    ].tail(20).to_string(index=False)
)


# ============================================================
# DISCOVER AVAILABLE MARKET TABLES
# ============================================================

tables = pd.read_sql(
    """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """,
    engine
)

print("\n--- AVAILABLE PUBLIC TABLES ---")
print(
    tables.to_string(index=False)
)

print(
    "\nIMPORTANT: We need to identify which table contains "
    "ticker/date/price data before recalculating the labels."
)