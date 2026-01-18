"""Tests for IngestionScheduler class."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.ingestor.scheduler import IngestionScheduler, start_scheduler


class TestIngestionScheduler:
    """Tests for IngestionScheduler class."""

    def test_initialization(self):
        """Test scheduler initialization."""
        mock_storage = MagicMock()
        
        with patch("src.ingestor.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(top_symbols=["BTC/USDT"])
            
            scheduler = IngestionScheduler(mock_storage)
            
            assert scheduler.storage == mock_storage
            assert scheduler.scheduler is not None

    def test_start_scheduler(self):
        """Test that start adds job and starts scheduler."""
        mock_storage = MagicMock()
        
        with patch("src.ingestor.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(top_symbols=["BTC/USDT"])
            
            scheduler = IngestionScheduler(mock_storage)
            
            with patch.object(scheduler.scheduler, 'add_job') as mock_add_job:
                with patch.object(scheduler.scheduler, 'start') as mock_start:
                    scheduler.start()
                    
                    mock_add_job.assert_called_once()
                    mock_start.assert_called_once()

    def test_stop_scheduler_calls_shutdown(self):
        """Test that stop calls shutdown when appropriate."""
        mock_storage = MagicMock()
        
        with patch("src.ingestor.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(top_symbols=["BTC/USDT"])
            
            scheduler = IngestionScheduler(mock_storage)
            
            # Mock the scheduler's internal state
            mock_internal_scheduler = MagicMock()
            mock_internal_scheduler.running = True
            scheduler.scheduler = mock_internal_scheduler
            
            scheduler.stop()
            mock_internal_scheduler.shutdown.assert_called_once_with(wait=False)

    def test_stop_scheduler_not_running(self):
        """Test stop does nothing when scheduler not running."""
        mock_storage = MagicMock()
        
        with patch("src.ingestor.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(top_symbols=["BTC/USDT"])
            
            scheduler = IngestionScheduler(mock_storage)
            
            # Mock the scheduler as not running
            mock_internal_scheduler = MagicMock()
            mock_internal_scheduler.running = False
            scheduler.scheduler = mock_internal_scheduler
            
            scheduler.stop()
            mock_internal_scheduler.shutdown.assert_not_called()


class TestStartSchedulerFunction:
    """Tests for start_scheduler convenience function."""

    def test_start_scheduler_function(self):
        """Test start_scheduler creates and starts scheduler."""
        mock_storage = MagicMock()
        
        with patch("src.ingestor.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(top_symbols=["BTC/USDT"])
            
            with patch.object(IngestionScheduler, 'start') as mock_start:
                scheduler = start_scheduler(mock_storage)
                
                assert isinstance(scheduler, IngestionScheduler)
                mock_start.assert_called_once()

