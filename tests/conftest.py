"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from privacy_filter import PrivacyFilter


@pytest.fixture(scope="module")
def filter_instance():
    """Create a shared PrivacyFilter instance for all tests"""
    return PrivacyFilter(use_gliner=True)


@pytest.fixture(scope="module")
def filter_no_gliner():
    """Create PrivacyFilter without GLiNER (regex only)"""
    return PrivacyFilter(use_gliner=False)


# Custom markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "email: email detection tests"
    )
    config.addinivalue_line(
        "markers", "phone: phone number detection tests"
    )
    config.addinivalue_line(
        "markers", "credit_card: credit card detection tests"
    )
    config.addinivalue_line(
        "markers", "ssn: SSN and national ID detection tests"
    )
    config.addinivalue_line(
        "markers", "crypto: cryptocurrency address detection tests"
    )
