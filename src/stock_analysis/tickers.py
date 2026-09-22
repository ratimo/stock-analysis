"""Ticker-universe loading and exchange-symbol normalisation."""

from __future__ import annotations

from pathlib import Path


REQUIRED_COLUMNS = {"Symbol"}


def to_yahoo_ticker(symbol: str) -> str:
    """Convert a Nasdaq Helsinki symbol to Yahoo Finance notation.

    Nasdaq may publish symbols such as ``NDA FI`` while Yahoo Finance uses
    ``NDA-FI.HE``. Existing exchange suffixes are preserved so the helper is
    safe to call both for raw Nasdaq symbols and already-normalised tickers.
    """
    value = str(symbol).strip().upper()
    if not value:
        raise ValueError("Ticker symbol cannot be empty")
    if value.endswith(".HE"):
        return value
    return f"{value.replace(' ', '-')}.HE"


def load_tickers(path: Path):
    """Load, validate and enrich the ticker universe used by the analysis.

    Duplicate or blank symbols are removed before the Yahoo Finance symbol is
    derived. The original columns are retained, allowing market-segment
    metadata from the input workbook to flow into the final dataset.
    """
    import pandas as pd

    # Keep the Excel dependency local to this function so lightweight helpers
    # remain importable in environments where pandas is not installed yet.
    frame = pd.read_excel(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Ticker file is missing columns: {sorted(missing)}")

    result = frame.copy()
    # Normalising once here prevents whitespace/case differences from creating
    # duplicate API requests or duplicate output rows.
    result["Symbol"] = result["Symbol"].astype(str).str.strip().str.upper()
    result = result[result["Symbol"].ne("")].drop_duplicates("Symbol").reset_index(drop=True)
    if result.empty:
        raise ValueError("Ticker file contains no usable symbols")
    result["YahooTicker"] = result["Symbol"].map(to_yahoo_ticker)
    return result
