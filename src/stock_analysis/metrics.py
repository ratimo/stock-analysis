"""Financial metric helpers used by the analysis pipeline.

The functions in this module deliberately return ``None`` when source data
is unavailable or a ratio is mathematically undefined. A missing financial
value is preferable to silently substituting zero and is preserved as a blank
cell in the final Excel dataset.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any


def percentage_change(value: float | None, baseline: float | None) -> float | None:
    """Return percentage change from ``baseline`` to ``value``.

    ``baseline`` is the denominator because the result answers: how much has
    the analysis-year value changed relative to the comparison-year value?
    """
    if value is None or baseline is None or baseline == 0:
        return None
    try:
        return float((value - baseline) / baseline * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def select_year_value(values: Mapping[Any, Any], year: int) -> Any | None:
    """Return the first value whose date-like column belongs to ``year``.

    yfinance normally exposes statement columns as timestamps, but this helper
    also accepts strings and other date-like labels. We select by calendar year
    instead of assuming every company reports on 31 December.
    """
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
    """Read a statement line item using aliases and fiscal year.

    Financial-statement labels vary between instruments and yfinance versions,
    so callers can provide fallback names in priority order.
    """
    for name in names:
        if name in statement.index:
            return select_year_value(statement.loc[name], year)
    return None


def safe_ratio(numerator: Any, denominator: Any) -> float | None:
    """Calculate a numeric ratio, returning ``None`` for unusable inputs."""
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
    """Calculate comparable metrics from one yfinance ticker.

    The calculations use the same fiscal year and the same year-end market
    price for each row. P/B uses book value per share; P/E uses EPS; ROE uses
    net income divided by equity; and dividend yield is expressed as a percent.
    """
    import pandas as pd

    # Fetch each statement once per ticker. This avoids repeated network calls
    # while keeping the metric formulas independent and readable.
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
    book_value = assets - liabilities if assets is not None and liabilities is not None else None
    book_value_per_share = safe_ratio(book_value, shares)

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
