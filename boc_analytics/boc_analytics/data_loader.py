"""
data_loader.py
Parses the BOC PostgreSQL dump file and returns clean DataFrames.
All results are cached with st.cache_data for fast re-use.
"""

import re
import json
import pandas as pd
import numpy as np
import streamlit as st
from io import StringIO
from pathlib import Path

# ── Data file path ────────────────────────────────────────────────────────────
# Supports both local Windows development and Streamlit Cloud (Linux) deployment.
# On Streamlit Cloud the file must be committed to the repo at boc_analytics/bocdata 1
_HERE = Path(__file__).parent                  # directory of data_loader.py
_RELATIVE = _HERE / "bocdata 1"               # repo-relative path (Streamlit Cloud)
_ABSOLUTE = Path(r"C:\BOC\bocdata 1")          # local Windows development path

if _RELATIVE.exists():
    DUMP_PATH = _RELATIVE
elif _ABSOLUTE.exists():
    DUMP_PATH = _ABSOLUTE
else:
    # Last resort: let it fail with a clear message
    DUMP_PATH = _RELATIVE

# ---------------------------------------------------------------------------
# Low-level dump parser
# ---------------------------------------------------------------------------

def _parse_dump(path: Path) -> dict[str, pd.DataFrame]:
    """
    Read the PostgreSQL dump and return a dict of {table_name: DataFrame}.
    Handles tab-separated COPY … FROM stdin blocks.
    """
    tables: dict[str, list[list[str]]] = {}
    columns: dict[str, list[str]] = {}

    col_pattern   = re.compile(
        r"^COPY public\.\"?(\w+)\"?\s*\(([^)]+)\)\s+FROM stdin;", re.MULTILINE
    )
    create_pattern = re.compile(
        r"CREATE TABLE public\.\"?(\w+)\"?\s*\(([\s\S]*?)\);", re.MULTILINE
    )

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    # ---- Extract column names from CREATE TABLE ----
    for m in create_pattern.finditer(content):
        tname = m.group(1)
        body  = m.group(2)
        cols  = []
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            if not line or line.upper().startswith(("CONSTRAINT", "PRIMARY", "UNIQUE", "CHECK")):
                continue
            # column name is first token, strip quotes
            col = line.split()[0].strip('"')
            cols.append(col)
        columns[tname] = cols

    # ---- Extract COPY data blocks ----
    # Split by COPY header
    copy_split = re.split(r"(COPY public\.\"?\w+\"?\s*\([^)]+\)\s+FROM stdin;)", content)

    i = 0
    while i < len(copy_split):
        chunk = copy_split[i]
        m = col_pattern.match(chunk.strip())
        if m and i + 1 < len(copy_split):
            tname = m.group(1)
            col_names_raw = [c.strip().strip('"') for c in m.group(2).split(",")]
            data_block = copy_split[i + 1]
            rows = []
            for line in data_block.splitlines():
                if line == "\\.":
                    break
                if line:
                    rows.append(line.split("\t"))
            tables[tname] = rows
            columns[tname] = col_names_raw  # prefer COPY column order
            i += 2
        else:
            i += 1

    # ---- Build DataFrames ----
    dfs: dict[str, pd.DataFrame] = {}
    for tname, rows in tables.items():
        cols = columns.get(tname, [])
        # Pad / trim rows to match column count
        n = len(cols)
        cleaned = []
        for row in rows:
            if len(row) < n:
                row = row + ["\\N"] * (n - len(row))
            cleaned.append(row[:n])
        df = pd.DataFrame(cleaned, columns=cols)
        # Replace PostgreSQL null marker
        df = df.replace("\\N", np.nan)
        dfs[tname] = df

    return dfs


# ---------------------------------------------------------------------------
# Public cached loader
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="⏳ Loading BOC database…")
def load_all() -> dict[str, pd.DataFrame]:
    dfs = _parse_dump(DUMP_PATH)

    # ---- bill ----
    if "bill" in dfs:
        b = dfs["bill"]
        b["createdAt"] = pd.to_datetime(b["createdAt"], errors="coerce", utc=True).dt.tz_convert(None)
        b["updatedAt"] = pd.to_datetime(b["updatedAt"], errors="coerce", utc=True).dt.tz_convert(None)
        dfs["bill"] = b

    # ---- bill_extraction ----
    if "bill_extraction" in dfs:
        be = dfs["bill_extraction"]
        be["totalAmount"]  = pd.to_numeric(be["totalAmount"],  errors="coerce")
        be["taxAmount"]    = pd.to_numeric(be["taxAmount"],    errors="coerce")
        be["invoiceDate"]  = pd.to_datetime(be["invoiceDate"], errors="coerce", utc=True).dt.tz_convert(None)
        be["createdAt"]    = pd.to_datetime(be["createdAt"],   errors="coerce", utc=True).dt.tz_convert(None)
        # Parse lineItems JSON
        def safe_json(v):
            try:
                return json.loads(v) if isinstance(v, str) else []
            except Exception:
                return []
        be["lineItems_parsed"] = be["lineItems"].apply(safe_json)
        dfs["bill_extraction"] = be

    # ---- user ----
    if "user" in dfs:
        u = dfs["user"]
        u["createdAt"]           = pd.to_datetime(u["createdAt"],    errors="coerce", utc=True).dt.tz_convert(None)
        u["rewardBalance"]       = pd.to_numeric(u["rewardBalance"],  errors="coerce").fillna(0)
        u["lifetimeRewardPoints"]= pd.to_numeric(u["lifetimeRewardPoints"], errors="coerce").fillna(0)
        dfs["user"] = u

    # ---- reward_credit ----
    if "reward_credit" in dfs:
        rc = dfs["reward_credit"]
        rc["amount"]    = pd.to_numeric(rc["amount"],    errors="coerce")
        rc["createdAt"] = pd.to_datetime(rc["createdAt"], errors="coerce", utc=True).dt.tz_convert(None)
        dfs["reward_credit"] = rc

    # ---- reward_claim ----
    if "reward_claim" in dfs:
        rcl = dfs["reward_claim"]
        rcl["amount"]    = pd.to_numeric(rcl["amount"],    errors="coerce")
        rcl["createdAt"] = pd.to_datetime(rcl["createdAt"], errors="coerce", utc=True).dt.tz_convert(None)
        dfs["reward_claim"] = rcl

    # ---- fraud_check ----
    if "fraud_check" in dfs:
        fc = dfs["fraud_check"]
        fc["score"]     = pd.to_numeric(fc["score"],     errors="coerce")
        fc["createdAt"] = pd.to_datetime(fc["createdAt"], errors="coerce", utc=True).dt.tz_convert(None)
        dfs["fraud_check"] = fc

    return dfs


# ---------------------------------------------------------------------------
# Convenience getters
# ---------------------------------------------------------------------------

def get_bills_with_extraction(dfs: dict) -> pd.DataFrame:
    """Join bill + bill_extraction + user for a rich fact table."""
    bill = dfs.get("bill", pd.DataFrame())
    be   = dfs.get("bill_extraction", pd.DataFrame())
    user = dfs.get("user", pd.DataFrame())[["id", "name", "email",
                                             "rewardBalance", "lifetimeRewardPoints",
                                             "createdAt"]].rename(
        columns={"id": "userId", "createdAt": "userCreatedAt", "name": "userName", "email": "userEmail"}
    )
    merged = bill.merge(be, left_on="id", right_on="billId", how="left", suffixes=("_bill", "_be"))
    merged = merged.merge(user, on="userId", how="left")
    return merged


CURRENCY_COUNTRY = {
    "IDR": "Indonesia", "INR": "India", "NGN": "Nigeria", "VND": "Vietnam",
    "PHP": "Philippines", "USD": "United States", "DZD": "Algeria",
    "PKR": "Pakistan", "TRY": "Turkey", "UAH": "Ukraine", "IRR": "Iran",
    "BDT": "Bangladesh", "GBP": "United Kingdom", "MYR": "Malaysia",
    "EUR": "Europe", "HKD": "Hong Kong", "MMK": "Myanmar", "BRL": "Brazil",
    "AED": "UAE", "CHF": "Switzerland", "ZAR": "South Africa", "ETB": "Ethiopia",
    "TWD": "Taiwan", "KES": "Kenya", "EGP": "Egypt", "THB": "Thailand",
    "JPY": "Japan", "UZS": "Uzbekistan", "XOF": "West Africa", "KHR": "Cambodia",
    "NPR": "Nepal", "CAD": "Canada", "RUB": "Russia", "MXN": "Mexico",
    "SGD": "Singapore", "PEN": "Peru", "AUD": "Australia", "PLN": "Poland",
    "NZD": "New Zealand", "MAD": "Morocco", "LKR": "Sri Lanka",
}

CURRENCY_ISO3 = {
    "IDR": "IDN", "INR": "IND", "NGN": "NGA", "VND": "VNM",
    "PHP": "PHL", "USD": "USA", "DZD": "DZA", "PKR": "PAK",
    "TRY": "TUR", "UAH": "UKR", "IRR": "IRN", "BDT": "BGD",
    "GBP": "GBR", "MYR": "MYS", "EUR": "DEU", "HKD": "HKG",
    "MMK": "MMR", "BRL": "BRA", "AED": "ARE", "CHF": "CHE",
    "ZAR": "ZAF", "ETB": "ETH", "TWD": "TWN", "KES": "KEN",
    "EGP": "EGY", "THB": "THA", "JPY": "JPN", "UZS": "UZB",
    "CAD": "CAN", "RUB": "RUS", "MXN": "MEX", "SGD": "SGP",
    "AUD": "AUS", "PLN": "POL", "NZD": "NZL", "MAD": "MAR",
    "LKR": "LKA",
}
