from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, text
from src.storage.db import get_db, AsyncSessionLocal
from src.storage.models import RawMarketData, ComputedMetrics
from typing import List, Dict, Any

router = APIRouter()

@router.get("/actuator/health", tags=["System"])
async def health_check():
    """System health check."""
    try:
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database Disconnected: {e}")

@router.get("/api/v1/market/{symbol}", tags=["Market Data"])
async def get_market_data(symbol: str, limit: int = 100):
    """Get raw OHLCV data."""
    # Normalize path safe symbol (BTC-USDT -> BTC/USDT)
    db_symbol = symbol.replace("-", "/")
    
    async for session in get_db():
        stmt = (
            select(RawMarketData)
            .where(RawMarketData.symbol == db_symbol)
            .order_by(RawMarketData.time.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "time": r.time,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume
            } 
            for r in rows
        ]

@router.get("/api/v1/metrics/{symbol}", tags=["Market Data"])
async def get_metrics(symbol: str, limit: int = 100):
    """Get computed technical metrics."""
    # Normalize path safe symbol
    db_symbol = symbol.replace("-", "/")

    async for session in get_db():
        stmt = (
            select(ComputedMetrics)
            .where(ComputedMetrics.symbol == db_symbol)
            .order_by(ComputedMetrics.time.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "time": r.time,
                "rsi_14": r.rsi_14,
                "macd_line": r.macd_line,
                "bb_width": r.bb_width,
                "z_score": r.z_score,
                "trend_adx": r.trend_adx
            } 
            for r in rows
        ]
