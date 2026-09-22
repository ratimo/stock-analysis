# OMX Helsinki stock analysis

The project produces one unified dataset from the Nasdaq Helsinki ticker universe. Data collection and metric calculations live in `src/stock_analysis`; the notebook is only a thin, reproducible user interface.

## Structure

- `Ticker_symbols.xlsx` — input universe. The first sheet contains the required `Symbol` column.
- `src/stock_analysis/tickers.py` — input validation and Yahoo Finance ticker conversion.
- `src/stock_analysis/metrics.py` — fiscal-year selection and metric calculations.
- `src/stock_analysis/pipeline.py` — concurrent download, row-level error handling, sorting, and final export.
- `fin_stock_analysis.ipynb` — recommended notebook.
- `tests/` — dependency-light tests for core transformations.

## Run locally

Use a native Python environment matching your machine architecture. The previous global Python installation had an x86_64/arm64 NumPy mismatch, so use a fresh virtual environment:

```bash
cd stock-analysis
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests -v
jupyter lab
```

Open `fin_stock_analysis.ipynb`, set the years in the configuration cell, and run all cells. The final dataset is written once to `stock_analysis_dataset.xlsx`.

## Run without the notebook

```bash
PYTHONPATH=src python - <<'PY'
from stock_analysis.config import AnalysisConfig
from stock_analysis.pipeline import run_analysis, save_dataset

config = AnalysisConfig(max_workers=4)
dataset = run_analysis(config)
save_dataset(dataset, config)
print(dataset.shape)
print(dataset['status'].value_counts(dropna=False))
PY
```

## Dataset contract

The `Dataset` sheet always contains one row per input ticker. Failed API requests are not silently dropped: they remain in the dataset with `status="error"` and the exception in `error`. This makes filtering and quality checks explicit. Numeric metrics are calculated for the configured analysis year; the comparison year is currently used for the year-end closing price.

The output contains revenue, EPS, P/B, P/E, dividend yield, debt-to-equity, ROE, and both year-end closing prices. Financial statement dates are selected by year rather than by assuming a string such as `YYYY-12-31`, which handles yfinance timestamp columns correctly.

`price_change_pct_from_comparison` measures the change from `comparison_year_last_close` to `analysis_year_last_close`:

```text
(analysis_year_last_close - comparison_year_last_close)
/ comparison_year_last_close * 100
```

Positive values indicate growth and negative values indicate decline. If the comparison price is missing or zero, the result is blank.

The pipeline uses yfinance and therefore requires network access. It does not guarantee that every listed instrument has historical financial statements; missing values are expected for some instruments and are represented as blank cells rather than fabricated values.
