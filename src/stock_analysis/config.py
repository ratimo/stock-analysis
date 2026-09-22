"""Analysis configuration and date defaults.

The defaults intentionally move with the calendar: the previous calendar year
is used for financial-statement metrics and the current year is used as the
comparison period for market prices.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class AnalysisConfig:
    """Runtime settings for one reproducible analysis run.

    All paths are relative to the directory from which the notebook or the
    command-line script is started unless an absolute path is supplied.
    ``frozen=True`` prevents accidental changes after a run has started.
    """

    # Input workbook containing the Nasdaq Helsinki ticker universe.
    ticker_file: Path = Path("Ticker_symbols.xlsx")
    # Financial year used for statements and the first closing-price column.
    analysis_year: int = date.today().year - 1
    # Current calendar year used for the comparison closing-price column.
    comparison_year: int = date.today().year
    # Number of concurrent Yahoo Finance requests.
    max_workers: int = 4
    # Single final output workbook; intermediate exports are not needed.
    output_file: Path = Path("stock_analysis_dataset.xlsx")
