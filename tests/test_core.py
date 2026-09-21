import unittest
from datetime import datetime

from stock_analysis.metrics import percentage_change, select_year_value
from stock_analysis.tickers import to_yahoo_ticker


class CoreTests(unittest.TestCase):
    def test_percentage_change_uses_comparison_value_as_baseline(self):
        self.assertEqual(percentage_change(120.0, 100.0), 20.0)

    def test_percentage_change_returns_none_for_missing_or_zero_baseline(self):
        self.assertIsNone(percentage_change(None, 100.0))
        self.assertIsNone(percentage_change(120.0, 0.0))

    def test_to_yahoo_ticker_handles_nordea_symbol_with_space(self):
        self.assertEqual(to_yahoo_ticker("NDA FI"), "NDA-FI.HE")


    def test_to_yahoo_ticker_does_not_duplicate_exchange_suffix(self):
        self.assertEqual(to_yahoo_ticker("YIT.HE"), "YIT.HE")


    def test_select_year_value_accepts_timestamp_columns(self):
        values = {
            datetime(2022, 12, 31): 123.0,
            datetime(2021, 12, 31): 99.0,
        }
        self.assertEqual(select_year_value(values, 2022), 123.0)


    def test_select_year_value_returns_none_when_year_is_missing(self):
        self.assertIsNone(select_year_value({}, 2022))
