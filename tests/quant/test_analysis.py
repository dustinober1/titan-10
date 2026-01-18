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

if __name__ == "__main__":
    unittest.main()
