from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnalysisConfig:
    """Runtime settings for one reproducible analysis run."""

    ticker_file: Path = Path("Ticker_symbols.xlsx")
    analysis_year: int = 2022
    comparison_year: int = 2023
    max_workers: int = 4
    output_file: Path = Path("stock_analysis_dataset.xlsx")
