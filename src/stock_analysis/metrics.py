from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any


def percentage_change(value: float | None, baseline: float | None) -> float | None:
    """Return percentage change from ``baseline`` to ``value``."""
    if value is None or baseline is None or baseline == 0:
        return None
    try:
        return float((value - baseline) / baseline * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def select_year_value(values: Mapping[Any, Any], year: int) -> Any | None:
    """Return the first value whose date-like column belongs to ``year``."""
    for column, value in values.items():
        try:
            if isinstance(column, (date, datetime)) and column.year == year:
                return value
            if str(column).startswith(str(year)):
                return value
        except (TypeError, ValueError):
            if str(column).startswith(str(year)):
                return value
    return None


def statement_value(statement: Any, names: tuple[str, ...], year: int) -> Any | None:
    """Read a financial-statement line item using aliases and fiscal year."""
    for name in names:
        if name in statement.index:
            return select_year_value(statement.loc[name], year)
    return None


def safe_ratio(numerator: Any, denominator: Any) -> float | None:
    import pandas as pd

    if numerator is None or denominator is None or denominator == 0:
        return None
    if pd.isna(numerator) or pd.isna(denominator):
        return None
    try:
        return float(numerator / denominator)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def calculate_metrics(ticker: Any, year: int, price: float | None) -> dict[str, float | None]:
    """Calculate comparable metrics from one yfinance Ticker object."""
    import pandas as pd

    income = ticker.income_stmt
    balance = ticker.balance_sheet
    financials = ticker.financials

    revenue = statement_value(income, ("Total Revenue",), year)
    eps = statement_value(financials, ("Basic EPS", "Diluted EPS"), year)
    net_income = statement_value(income, ("Net Income", "Net Income Common Stockholders"), year)
    equity = statement_value(balance, ("Total Equity Gross Minority Interest", "Stockholders Equity"), year)
    assets = statement_value(balance, ("Total Assets",), year)
    liabilities = statement_value(
        balance,
        ("Total Liabilities Net Minority Interest", "Total Liab"),
        year,
    )

    shares = None
    try:
        shares = ticker.fast_info.get("shares")
    except Exception:
        shares = None
    book_value_per_share = safe_ratio((assets or 0) - (liabilities or 0), shares) if assets is not None and liabilities is not None else None

    dividend_yield = None
    try:
        dividends = ticker.dividends
        dividends.index = pd.to_datetime(dividends.index)
        annual_dividends = dividends[dividends.index.year == year].sum()
        dividend_yield = safe_ratio(annual_dividends * 100, price)
    except Exception:
        dividend_yield = None

    return {
        "total_revenue": float(revenue) if revenue is not None and not pd.isna(revenue) else None,
        "eps": float(eps) if eps is not None and not pd.isna(eps) else None,
        "pb_ratio": safe_ratio(price, book_value_per_share),
        "pe_ratio": safe_ratio(price, eps),
        "dividend_yield_pct": dividend_yield,
        "debt_to_equity": safe_ratio(liabilities, equity),
        "roe": safe_ratio(net_income, equity),
    }
