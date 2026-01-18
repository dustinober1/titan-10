"""Tests for FastAPI API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.api.main import app


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_success(self):
        """Test successful health check."""
        with patch("src.api.routes.get_db") as mock_get_db:
            # Mock the database session
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            client = TestClient(app)
            response = client.get("/actuator/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["database"] == "connected"

    def test_health_check_db_failure(self):
        """Test health check when database is down."""
        with patch("src.api.routes.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=Exception("Connection refused"))
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            client = TestClient(app)
            response = client.get("/actuator/health")
            
            assert response.status_code == 503
            assert "Disconnected" in response.json()["detail"]


class TestMarketDataEndpoint:
    """Tests for market data endpoint."""

    def test_get_market_data_success(self):
        """Test successful market data retrieval."""
        mock_data = [
            MagicMock(
                time=datetime(2024, 1, 1, 12, 0, 0),
                open=42000.0,
                high=42500.0,
                low=41800.0,
                close=42300.0,
                volume=1000.0,
            ),
        ]
        
        with patch("src.api.routes.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_data
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            client = TestClient(app)
            response = client.get("/api/v1/market/BTC-USDT")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["open"] == 42000.0
            assert data[0]["close"] == 42300.0

    def test_symbol_normalization(self):
        """Test that hyphenated symbols are normalized to slashes."""
        with patch("src.api.routes.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            client = TestClient(app)
            response = client.get("/api/v1/market/BTC-USDT?limit=50")
            
            assert response.status_code == 200
            # The query should have been made with BTC/USDT
            call_args = mock_session.execute.call_args
            assert call_args is not None

    def test_get_market_data_empty(self):
        """Test market data for symbol with no data."""
        with patch("src.api.routes.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            client = TestClient(app)
            response = client.get("/api/v1/market/UNKNOWN-PAIR")
            
            assert response.status_code == 200
            assert response.json() == []


class TestMetricsEndpoint:
    """Tests for computed metrics endpoint."""

    def test_get_metrics_success(self):
        """Test successful metrics retrieval."""
        mock_metrics = [
            MagicMock(
                time=datetime(2024, 1, 1, 12, 0, 0),
                rsi_14=55.0,
                macd_line=100.0,
                bb_width=0.05,
                z_score=0.5,
                trend_adx=25.0,
            ),
        ]
        
        with patch("src.api.routes.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_metrics
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            client = TestClient(app)
            response = client.get("/api/v1/metrics/ETH-USDT")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["rsi_14"] == 55.0
            assert data[0]["z_score"] == 0.5

    def test_get_metrics_with_limit(self):
        """Test metrics retrieval with custom limit."""
        with patch("src.api.routes.get_db") as mock_get_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            client = TestClient(app)
            response = client.get("/api/v1/metrics/BTC-USDT?limit=25")
            
            assert response.status_code == 200


# Note: Debug endpoint tests removed as StaticFiles mount catches these routes
# The /debug/{path} endpoint is for development debugging only
