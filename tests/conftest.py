"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from researchtopodcast.settings import Settings
    return Settings(
        openrouter_api_key="test-key",
        podgen_temp_dir=Path("./test_output")
    )
