from __future__ import annotations

from pathlib import Path


REQUIRED_COLUMNS = {"Symbol"}


def to_yahoo_ticker(symbol: str) -> str:
    """Convert a Nasdaq Helsinki symbol to Yahoo Finance notation."""
    value = str(symbol).strip().upper()
    if not value:
        raise ValueError("Ticker symbol cannot be empty")
    if value.endswith(".HE"):
        return value
    return f"{value.replace(' ', '-')}.HE"


def load_tickers(path: Path):
    """Load and validate the ticker universe used by the analysis."""
    import pandas as pd

    frame = pd.read_excel(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Ticker file is missing columns: {sorted(missing)}")

    result = frame.copy()
    result["Symbol"] = result["Symbol"].astype(str).str.strip().str.upper()
    result = result[result["Symbol"].ne("")].drop_duplicates("Symbol").reset_index(drop=True)
    if result.empty:
        raise ValueError("Ticker file contains no usable symbols")
    result["YahooTicker"] = result["Symbol"].map(to_yahoo_ticker)
    return result
