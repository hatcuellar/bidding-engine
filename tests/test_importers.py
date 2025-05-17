"""
Unit tests for data import functionality to ensure idempotency
and correct behavior under various conditions.
"""

import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules to test
from scripts.import_performance_data import (
    import_performance_data,
    parse_performance_file,
    validate_performance_data,
    deduplicate_events
)
from models import EventLog, BidHistory

# Test fixtures
@pytest.fixture
def sample_performance_data():
    """Sample performance data for testing imports"""
    return [
        {
            "event_id": "evt_12345",
            "type": "impression",
            "brand_id": 100,
            "partner_id": 200,
            "ad_slot_id": 300,
            "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "metadata": {"device": "mobile", "position": "top"}
        },
        {
            "event_id": "evt_12346",
            "type": "click",
            "brand_id": 100,
            "partner_id": 200,
            "ad_slot_id": 300,
            "timestamp": (datetime.utcnow() - timedelta(hours=23)).isoformat(),
            "metadata": {"device": "mobile", "position": "top"}
        },
        {
            "event_id": "evt_12347",
            "type": "conversion",
            "brand_id": 100,
            "partner_id": 200,
            "ad_slot_id": 300,
            "timestamp": (datetime.utcnow() - timedelta(hours=22)).isoformat(),
            "metadata": {"device": "mobile", "position": "top"},
            "revenue": 15.75
        }
    ]

@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    mock_session = MagicMock(spec=Session)
    
    # Setup mock query results
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    
    # Default: no existing events in DB
    mock_filter.first.return_value = None
    
    return mock_session

def test_parse_performance_file():
    """Test parsing performance data from file"""
    # Mock file content
    mock_data = [
        {"event_id": "evt_12345", "type": "impression", "brand_id": 100},
        {"event_id": "evt_12346", "type": "click", "brand_id": 100}
    ]
    mock_file_content = json.dumps(mock_data)
    
    # Test with mock file
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        result = parse_performance_file("dummy_path.json")
        
        # Check result
        assert len(result) == 2
        assert result[0]["event_id"] == "evt_12345"
        assert result[1]["type"] == "click"

def test_validate_performance_data(sample_performance_data):
    """Test data validation logic"""
    # Valid data should pass
    valid_result = validate_performance_data(sample_performance_data)
    assert valid_result is True
    
    # Invalid data (missing required field)
    invalid_data = sample_performance_data.copy()
    invalid_data.append({"type": "impression"})  # Missing event_id
    
    with pytest.raises(ValueError):
        validate_performance_data(invalid_data)

def test_deduplicate_events(sample_performance_data, mock_db_session):
    """Test deduplication of events"""
    # First run should accept all events
    new_events = deduplicate_events(sample_performance_data, mock_db_session)
    assert len(new_events) == 3
    
    # Setup mock to simulate existing events in DB
    def side_effect_exists(event_id):
        # Make first event exist in DB, others don't
        if event_id == "evt_12345":
            mock_event = MagicMock(spec=EventLog)
            mock_event.event_id = "evt_12345"
            return mock_event
        return None
    
    mock_db_session.query.return_value.filter.return_value.first.side_effect = side_effect_exists
    
    # Run again, should skip the existing event
    new_events = deduplicate_events(sample_performance_data, mock_db_session)
    assert len(new_events) == 2
    assert new_events[0]["event_id"] == "evt_12346"

def test_import_performance_data_idempotency(sample_performance_data, mock_db_session):
    """Test that import is idempotent (no duplicates)"""
    # First import
    result = import_performance_data(sample_performance_data, mock_db_session)
    assert result["imported_count"] == 3
    
    # Setup mock to simulate all events already in DB
    mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock(spec=EventLog)
    
    # Second import should not add duplicates
    result = import_performance_data(sample_performance_data, mock_db_session)
    assert result["imported_count"] == 0
    assert result["skipped_count"] == 3

def test_import_handles_invalid_data(mock_db_session):
    """Test that import handles invalid data gracefully"""
    invalid_data = [{"not_a_valid_event": True}]
    
    with pytest.raises(ValueError):
        import_performance_data(invalid_data, mock_db_session)
    
    # Verify no data was committed
    mock_db_session.commit.assert_not_called()