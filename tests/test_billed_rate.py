# tests/test_billed_rate.py

import unittest
import pandas as pd
from kpi_engine import billed_rate

class TestBilledRate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            pnl_path = "sample_data/LnTPnL.xlsx"
            ut_path = "sample_data/LNTData.xlsx"
            cls.pnl_df, cls.ut_df = billed_rate.load_data(pnl_path, ut_path)
        except Exception as e:
            raise RuntimeError(f"Setup failed: {e}")

    def test_load_data(self):
        self.assertIsInstance(self.pnl_df, pd.DataFrame)
        self.assertIsInstance(self.ut_df, pd.DataFrame)
        self.assertFalse(self.pnl_df.empty)
        self.assertFalse(self.ut_df.empty)

    def test_calculate_billed_rate(self):
        result = billed_rate.calculate_billed_rate(self.pnl_df, self.ut_df)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    def test_zero_billable_hours(self):
        ut_df_zero = self.ut_df.copy()
        ut_df_zero["TotalBillableHours"] = 0
        result = billed_rate.calculate_billed_rate(self.pnl_df, ut_df_zero)
        self.assertEqual(result, 0.0)

if __name__ == '__main__':
    unittest.main()
