import logging
import pandas as pd
import ta
import numpy as np
from sqlalchemy import select

from src.storage.db import AsyncSessionLocal
from src.storage.models import RawMarketData, ComputedMetrics

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """
    Quantitative Analysis Engine.
    Calculates technical indicators and statistical metrics using 'ta' library.
    """
    
    async def calculate_metrics(self, symbol: str, session) -> int:
        """
        Load recent data for symbol, calculate metrics, and persist result.
        Returns number of rows processed/updated.
        """
        try:
            # 1. Load Data
            # Fetch enough history for largest window (ZScore: 30) + buffer
            stmt = (
                select(RawMarketData)
                .where(RawMarketData.symbol == symbol)
                .order_by(RawMarketData.time.desc())
                .limit(500)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            
            if len(rows) < 30:
                logger.warning(f"Insufficient data for {symbol} analysis. Rows: {len(rows)}")
                return 0

            # Convert to DataFrame (reverse to have oldest first)
            data = [
                {
                    "time": r.time,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume
                } 
                for r in reversed(rows)
            ]
            df = pd.DataFrame(data)
            df.set_index("time", inplace=True)
            
            # 2. Calculate Technical Indicators & Statistical Metrics (Pure Logic)
            df = self._calculate_indicators(df)
            
            # 4. Persist Results (Upsert)
            
            metrics_objects = []
            
            # Iterate through the DataFrame to create model objects
            for idx, row in df.iterrows():
                
                # Handling NaN for float columns
                def get_val(val):
                    return None if pd.isna(val) else float(val)

                metric = ComputedMetrics(
                    time=idx, # index is datetime
                    symbol=symbol,
                    rsi_14=get_val(row.get("rsi_14")),
                    macd_line=get_val(row.get("macd_line")),
                    macd_signal=get_val(row.get("macd_signal")),
                    macd_hist=get_val(row.get("macd_hist")),
                    bb_upper=get_val(row.get("bb_upper")),
                    bb_lower=get_val(row.get("bb_lower")),
                    bb_width=get_val(row.get("bb_width")),
                    trend_adx=get_val(row.get("trend_adx")),
                    z_score=get_val(row.get("z_score")),
                    log_return=get_val(row.get("log_return"))
                )
                metrics_objects.append(metric)
            
            # Save last 50 for now
            count = 0
            for obj in metrics_objects[-50:]: 
                await session.merge(obj)
                count += 1
                
            await session.commit()
            return count

        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            raise

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pure function to calculate indicators on a DataFrame.
        """
        # RSI (14)
        df["rsi_14"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
        
        # MACD (12, 26, 9)
        macd = ta.trend.MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
        df["macd_line"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_hist"] = macd.macd_diff()
        
        # Bollinger Bands (20, 2)
        bb_indicator = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)
        df["bb_upper"] = bb_indicator.bollinger_hband()
        df["bb_lower"] = bb_indicator.bollinger_lband()
        # BB Width
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_lower"]
        
        # ADX (14)
        adx_indicator = ta.trend.ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=14)
        df["trend_adx"] = adx_indicator.adx()
            
        # Statistical Metrics
        
        # Log Returns
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
        
        # Z-Score (30d rolling window on close price)
        rolling_mean = df["close"].rolling(window=30).mean()
        rolling_std = df["close"].rolling(window=30).std()
        df["z_score"] = (df["close"] - rolling_mean) / rolling_std
        
        return df
