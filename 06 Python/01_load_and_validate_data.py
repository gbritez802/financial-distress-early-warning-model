import pandas as pd
import numpy as np
import sklearn
import sqlalchemy

print("Python modeling environment is ready.")
print("pandas:", pd.__version__)
print("numpy:", np.__version__)
print("scikit-learn:", sklearn.__version__)
print("SQLAlchemy:", sqlalchemy.__version__)
from sqlalchemy import create_engine
from getpass import getpass

# Ask for PostgreSQL password without storing it in the script
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

print("\nDatabase connection successful.")
print("Dataset shape:", df.shape)
print("\nSplit counts:")
print(df["dataset_split"].value_counts())
# ============================================================
# DATA VALIDATION
# ============================================================

print("\n--- DATA TYPES ---")
print(df.dtypes)

print("\n--- TARGET DISTRIBUTION ---")
print(df["distress_12m"].value_counts(dropna=False))

print("\n--- MISSING VALUES ---")
print(df.isna().sum())

print("\n--- DATE RANGES BY SPLIT ---")
print(
    df.groupby("dataset_split")["filed"]
      .agg(["min", "max", "count"])
)

print("\n--- DUPLICATE ROWS ---")
print("Exact duplicate rows:", df.duplicated().sum())