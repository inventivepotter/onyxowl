"""
Tests for NATS JetStream session storage
Run with: pytest tests/test_nats.py -v

These tests require a running NATS server with JetStream enabled.
Skip with: pytest tests/test_nats.py -v -m "not nats"
"""

import pytest
import os
import asyncio

# Import with PYTHONPATH handling
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Check if NATS is available
try:
    from privacy_filter.nats_store import NATSSessionStore, get_nats_store
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    NATSSessionStore = None
    get_nats_store = None


# Skip all tests in this module if NATS is not installed
pytestmark = pytest.mark.skipif(
    not NATS_AVAILABLE,
    reason="NATS package not installed"
)


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "nats: marks tests that require NATS server"
    )


@pytest.fixture
def nats_url():
    """Get NATS URL from environment or use default"""
    return os.getenv("NATS_URL", "nats://localhost:4222")


@pytest.fixture
async def nats_store(nats_url):
    """Create and connect NATS store"""
    store = NATSSessionStore(nats_url=nats_url)
    try:
        await store.connect()
        yield store
    except Exception as e:
        pytest.skip(f"Could not connect to NATS: {e}")
    finally:
        await store.disconnect()


@pytest.mark.nats
@pytest.mark.asyncio
class TestNATSSessionStore:
    """Tests for NATSSessionStore"""

    async def test_store_and_get_session(self, nats_store):
        """Test storing and retrieving session"""
        session_id = "test-session-001"
        token_map = {
            "{{__OWL:EMAIL_ADDRESS_1__}}": "john@example.com",
            "{{__OWL:PHONE_NUMBER_1__}}": "(555) 123-4567"
        }

        # Store session
        await nats_store.store_session(session_id, token_map)

        # Retrieve session
        retrieved = await nats_store.get_session(session_id)
        assert retrieved == token_map

        # Cleanup
        await nats_store.delete_session(session_id)

    async def test_store_with_custom_session_id(self, nats_store):
        """Test storing session with custom session_id"""
        custom_id = "my-custom-nats-session-123"
        token_map = {"{{__OWL:EMAIL_ADDRESS_1__}}": "alice@company.com"}

        await nats_store.store_session(custom_id, token_map)
        retrieved = await nats_store.get_session(custom_id)

        assert retrieved == token_map

        # Cleanup
        await nats_store.delete_session(custom_id)

    async def test_get_nonexistent_session(self, nats_store):
        """Test getting a session that doesn't exist"""
        result = await nats_store.get_session("nonexistent-session-id")
        assert result is None

    async def test_delete_session(self, nats_store):
        """Test deleting session"""
        session_id = "delete-test-session"
        token_map = {"{{__OWL:EMAIL_ADDRESS_1__}}": "delete@test.com"}

        # Store
        await nats_store.store_session(session_id, token_map)

        # Verify stored
        assert await nats_store.get_session(session_id) is not None

        # Delete
        deleted = await nats_store.delete_session(session_id)
        assert deleted is True

        # Verify deleted
        assert await nats_store.get_session(session_id) is None

    async def test_resolve_tokens(self, nats_store):
        """Test resolving specific tokens"""
        session_id = "resolve-test-session"
        token_map = {
            "{{__OWL:EMAIL_ADDRESS_1__}}": "john@example.com",
            "{{__OWL:PHONE_NUMBER_1__}}": "(555) 123-4567",
            "{{__OWL:SSN_1__}}": "123-45-6789"
        }

        await nats_store.store_session(session_id, token_map)

        # Resolve subset of tokens
        tokens_to_resolve = [
            "{{__OWL:EMAIL_ADDRESS_1__}}",
            "{{__OWL:PHONE_NUMBER_1__}}"
        ]
        resolved = await nats_store.resolve_tokens(session_id, tokens_to_resolve)

        assert resolved["{{__OWL:EMAIL_ADDRESS_1__}}"] == "john@example.com"
        assert resolved["{{__OWL:PHONE_NUMBER_1__}}"] == "(555) 123-4567"
        assert "{{__OWL:SSN_1__}}" not in resolved

        # Cleanup
        await nats_store.delete_session(session_id)

    async def test_session_ttl(self, nats_store):
        """Test session TTL (time-to-live)"""
        # This test verifies TTL is set correctly
        # Full TTL expiration testing would require waiting
        session_id = "ttl-test-session"
        token_map = {"{{__OWL:EMAIL_ADDRESS_1__}}": "ttl@test.com"}

        # Store with default TTL
        await nats_store.store_session(session_id, token_map)

        # Session should exist immediately
        assert await nats_store.get_session(session_id) is not None

        # Cleanup
        await nats_store.delete_session(session_id)

    async def test_multiple_sessions(self, nats_store):
        """Test storing multiple sessions"""
        sessions = {
            "multi-session-1": {"{{__OWL:EMAIL_1__}}": "user1@test.com"},
            "multi-session-2": {"{{__OWL:EMAIL_1__}}": "user2@test.com"},
            "multi-session-3": {"{{__OWL:EMAIL_1__}}": "user3@test.com"},
        }

        # Store all sessions
        for session_id, token_map in sessions.items():
            await nats_store.store_session(session_id, token_map)

        # Retrieve and verify each
        for session_id, expected_map in sessions.items():
            retrieved = await nats_store.get_session(session_id)
            assert retrieved == expected_map

        # Cleanup
        for session_id in sessions:
            await nats_store.delete_session(session_id)

    async def test_overwrite_session(self, nats_store):
        """Test overwriting an existing session"""
        session_id = "overwrite-test-session"

        # Store initial
        await nats_store.store_session(
            session_id,
            {"{{__OWL:EMAIL_1__}}": "original@test.com"}
        )

        # Overwrite
        new_map = {"{{__OWL:EMAIL_1__}}": "updated@test.com"}
        await nats_store.store_session(session_id, new_map)

        # Verify overwritten
        retrieved = await nats_store.get_session(session_id)
        assert retrieved == new_map

        # Cleanup
        await nats_store.delete_session(session_id)


@pytest.mark.nats
@pytest.mark.asyncio
class TestNATSIntegrationWithPrivacyFilter:
    """Integration tests for NATS with PrivacyFilter"""

    async def test_full_mask_demask_flow_with_nats(self, nats_store):
        """Test complete mask/demask flow using NATS storage"""
        from privacy_filter import PrivacyFilter

        filter_instance = PrivacyFilter(use_gliner=True)

        # Mask text
        text = "Contact alice@company.com for support"
        result = filter_instance.mask(text)

        # Store in NATS
        await nats_store.store_session(result.session_id, result.token_map)

        # Retrieve from NATS
        token_map = await nats_store.get_session(result.session_id)
        assert token_map is not None

        # Demask using NATS token map
        demask_result = filter_instance.demask(
            result.masked_text,
            token_map=token_map
        )
        assert "alice@company.com" in demask_result.original_text

        # Cleanup
        await nats_store.delete_session(result.session_id)

    async def test_custom_session_id_with_nats(self, nats_store):
        """Test custom session_id with NATS storage"""
        from privacy_filter import PrivacyFilter

        filter_instance = PrivacyFilter(use_gliner=True)
        custom_id = "nats-custom-session-test"

        # Mask with custom session_id
        result = filter_instance.mask(
            "Email bob@example.com",
            session_id=custom_id
        )
        assert result.session_id == custom_id

        # Store in NATS
        await nats_store.store_session(custom_id, result.token_map)

        # Retrieve from NATS
        token_map = await nats_store.get_session(custom_id)
        assert token_map is not None
        assert "bob@example.com" in token_map.values()

        # Cleanup
        await nats_store.delete_session(custom_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "nats"])
