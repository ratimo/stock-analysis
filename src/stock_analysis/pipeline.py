from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from .config import AnalysisConfig
from .metrics import calculate_metrics, percentage_change
from .tickers import load_tickers

LOGGER = logging.getLogger(__name__)


def _last_close(ticker: Any, year: int) -> float | None:
    history = ticker.history(start=f"{year}-01-01", end=f"{year + 1}-01-01", auto_adjust=False)
    if history.empty or "Close" not in history:
        return None
    return float(history["Close"].dropna().iloc[-1])


def _analyse_one(row: dict[str, Any], config: AnalysisConfig) -> dict[str, Any]:
    symbol = row["Symbol"]
    yahoo_ticker = row["YahooTicker"]
    result: dict[str, Any] = {
        "symbol": symbol,
        "yahoo_ticker": yahoo_ticker,
        "market_segment": row.get("Market Segment"),
        "name": row.get("Name"),
        "analysis_year": config.analysis_year,
        "comparison_year": config.comparison_year,
        "status": "ok",
        "error": None,
    }
    try:
        ticker = yf.Ticker(yahoo_ticker)
        analysis_price = _last_close(ticker, config.analysis_year)
        comparison_price = _last_close(ticker, config.comparison_year)
        result.update(calculate_metrics(ticker, config.analysis_year, analysis_price))
        result.update({
            "analysis_year_last_close": analysis_price,
            "comparison_year_last_close": comparison_price,
            "price_change_pct_from_comparison": percentage_change(
                analysis_price,
                comparison_price,
            ),
        })
    except Exception as exc:  # one bad instrument must not discard the dataset
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("Failed to analyse %s: %s", yahoo_ticker, exc)
    return result


def run_analysis(config: AnalysisConfig) -> pd.DataFrame:
    """Fetch the complete universe and return one row per input ticker."""
    tickers = load_tickers(config.ticker_file)
    rows = tickers.to_dict("records")
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        futures = [executor.submit(_analyse_one, row, config) for row in rows]
        for future in as_completed(futures):
            results.append(future.result())

    columns = [
        "symbol", "yahoo_ticker", "market_segment", "name", "analysis_year", "comparison_year",
        "status", "error", "total_revenue", "eps", "pb_ratio", "pe_ratio",
        "dividend_yield_pct", "debt_to_equity", "roe", "analysis_year_last_close",
        "comparison_year_last_close", "price_change_pct_from_comparison",
    ]
    return pd.DataFrame(results, columns=columns).sort_values("symbol").reset_index(drop=True)


def save_dataset(dataset: pd.DataFrame, config: AnalysisConfig) -> Path:
    """Save the final dataset once, with a small reproducibility sheet."""
    output = Path(config.output_file)
    metadata = pd.DataFrame([{
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "ticker_file": str(config.ticker_file),
        "analysis_year": config.analysis_year,
        "comparison_year": config.comparison_year,
        "rows": len(dataset),
        "successful_rows": int((dataset["status"] == "ok").sum()),
    }])
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataset.to_excel(writer, sheet_name="Dataset", index=False)
        metadata.to_excel(writer, sheet_name="Run_metadata", index=False)
    return output
