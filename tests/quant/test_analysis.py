import unittest
import pandas as pd
import numpy as np
from src.quant.analysis import AnalysisEngine

class TestAnalysisMath(unittest.TestCase):
    def setUp(self):
        self.engine = AnalysisEngine()
        
        # Create a dummy DataFrame with specific patterns to test indicators
        # Sine wave for price to have clear trends and mean reversion
        x = np.linspace(0, 100, 200)
        prices = 100 + 10 * np.sin(x/5)
        
        data = {
            "close": prices,
            "high": prices + 1,
            "low": prices - 1,
            "open": prices, # simplify
            "volume": np.random.randint(100, 1000, 200)
        }
        self.df = pd.DataFrame(data)
        
    def test_indicators_existence(self):
        """Test that all indicators columns are created."""
        df_out = self.engine._calculate_indicators(self.df.copy())
        
        expected_cols = [
            "rsi_14", "macd_line", "macd_signal", "macd_hist",
            "bb_upper", "bb_lower", "bb_width",
            "trend_adx", "z_score", "log_return"
        ]
        
        for col in expected_cols:
            self.assertIn(col, df_out.columns)
            
    def test_values_range(self):
        """Test that indicator values fall within expected ranges."""
        df_out = self.engine._calculate_indicators(self.df.copy())
        
        # RSI should be between 0 and 100
        # Ignore first 14 rows which are NaN
        rsi = df_out["rsi_14"].dropna()
        self.assertTrue(((rsi >= 0) & (rsi <= 100)).all())
        
        # BB Width should be positive (for valid BBs where upper > lower)
        bbw = df_out["bb_width"].dropna()
        self.assertTrue((bbw >= 0).all())

    def test_log_return_calculation(self):
        """Test that log returns are calculated correctly."""
        df_out = self.engine._calculate_indicators(self.df.copy())
        
        # First log return should be NaN (no previous value)
        self.assertTrue(pd.isna(df_out["log_return"].iloc[0]))
        
        # Log returns should exist for subsequent rows
        log_returns = df_out["log_return"].dropna()
        self.assertTrue(len(log_returns) > 0)
        
        # Verify manual calculation for second row
        expected_log_return = np.log(self.df["close"].iloc[1] / self.df["close"].iloc[0])
        actual_log_return = df_out["log_return"].iloc[1]
        self.assertAlmostEqual(actual_log_return, expected_log_return, places=10)

    def test_z_score_calculation(self):
        """Test that z-score is calculated with 30-day rolling window."""
        df_out = self.engine._calculate_indicators(self.df.copy())
        
        # First 29 z-scores should be NaN (need 30 days)
        z_scores_first_30 = df_out["z_score"].iloc[:29]
        self.assertTrue(z_scores_first_30.isna().all())
        
        # Z-scores after 30 rows should have values
        z_scores_after_30 = df_out["z_score"].iloc[30:].dropna()
        self.assertTrue(len(z_scores_after_30) > 0)
        
        # Z-scores should typically be between -3 and 3 for normal data
        # (with sine wave data this should hold)
        z_valid = df_out["z_score"].dropna()
        self.assertTrue(((z_valid >= -5) & (z_valid <= 5)).all())

    def test_adx_bounds(self):
        """Test that ADX values are within expected bounds."""
        df_out = self.engine._calculate_indicators(self.df.copy())
        
        # ADX should be between 0 and 100
        adx = df_out["trend_adx"].dropna()
        self.assertTrue(((adx >= 0) & (adx <= 100)).all())

    def test_macd_components(self):
        """Test that MACD components are calculated."""
        df_out = self.engine._calculate_indicators(self.df.copy())
        
        # MACD histogram should equal line minus signal
        macd_valid = df_out[["macd_line", "macd_signal", "macd_hist"]].dropna()
        
        if len(macd_valid) > 0:
            expected_hist = macd_valid["macd_line"] - macd_valid["macd_signal"]
            np.testing.assert_array_almost_equal(
                macd_valid["macd_hist"].values,
                expected_hist.values,
                decimal=10
            )

    def test_bollinger_bands_relationship(self):
        """Test that bb_upper > bb_lower always."""
        df_out = self.engine._calculate_indicators(self.df.copy())
        
        bb_valid = df_out[["bb_upper", "bb_lower"]].dropna()
        self.assertTrue((bb_valid["bb_upper"] > bb_valid["bb_lower"]).all())


