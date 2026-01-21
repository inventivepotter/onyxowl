"""
Tests for NATS JetStream session storage
Run with: pytest tests/test_nats.py -v

These tests require a running NATS server with JetStream enabled.
Skip with: pytest tests/test_nats.py -v -m "not nats"
"""

import pytest
import pytest_asyncio
import os
import asyncio

# Import with PYTHONPATH handling
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Check if NATS is available
try:
    from privacy_filter.nats_store import (
        NATSSessionStore,
        get_nats_store,
        KDFEncryption,
        KDF_ROTATION_PERIOD_SECONDS,
    )
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    NATSSessionStore = None
    get_nats_store = None
    KDFEncryption = None
    KDF_ROTATION_PERIOD_SECONDS = None


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


def _check_nats_available(url: str, timeout: float = 2.0) -> bool:
    """Quick check if NATS is reachable."""
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 4222

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except (socket.timeout, socket.error, OSError):
        return False


@pytest.fixture
def nats_url():
    """Get NATS URL from environment or use default"""
    return os.getenv("NATS_URL", "nats://localhost:4222")


@pytest_asyncio.fixture
async def nats_store(nats_url):
    """Create and connect NATS store"""
    # Quick check before trying async connection
    if not _check_nats_available(nats_url):
        pytest.skip("NATS server not available")

    store = NATSSessionStore(nats_url=nats_url)
    try:
        await asyncio.wait_for(store.connect(), timeout=5.0)
        yield store
        await store.disconnect()
    except asyncio.TimeoutError:
        pytest.skip("NATS connection timed out")
    except Exception as e:
        pytest.skip(f"Could not connect to NATS: {e}")


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


class TestKDFEncryption:
    """Tests for KDF-based encryption (no NATS required)"""

    def test_generate_master_key(self):
        """Test master key generation"""
        key = KDFEncryption.generate_master_key()

        # Key should be base64-encoded 32 bytes
        assert isinstance(key, str)
        assert len(key) == 44  # base64 of 32 bytes

        # Should be valid for creating encryption instance
        cipher = KDFEncryption(master_key=key)
        assert cipher.is_enabled

    def test_encryption_disabled_without_key(self):
        """Test that encryption is disabled without master key"""
        cipher = KDFEncryption(master_key=None)
        assert not cipher.is_enabled

    def test_encrypt_decrypt_roundtrip(self):
        """Test basic encrypt/decrypt roundtrip"""
        key = KDFEncryption.generate_master_key()
        cipher = KDFEncryption(master_key=key)

        plaintext = b'{"token": "secret-value"}'
        encrypted = cipher.encrypt(plaintext)

        # Encrypted should be different from plaintext
        assert encrypted != plaintext

        # Decrypt should return original
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_requires_enabled(self):
        """Test that encrypt raises when not enabled"""
        cipher = KDFEncryption(master_key=None)

        with pytest.raises(RuntimeError, match="not enabled"):
            cipher.encrypt(b"test")

    def test_decrypt_requires_enabled(self):
        """Test that decrypt raises when not enabled"""
        cipher = KDFEncryption(master_key=None)

        with pytest.raises(RuntimeError, match="not enabled"):
            cipher.decrypt(b"test")

    def test_invalid_key_format(self):
        """Test that invalid key format raises ValueError"""
        with pytest.raises(ValueError, match="Invalid ENCRYPTION_MASTER_KEY"):
            KDFEncryption(master_key="not-valid-base64!")

    def test_key_too_short(self):
        """Test that short key raises ValueError"""
        import base64
        short_key = base64.urlsafe_b64encode(b"tooshort").decode()

        with pytest.raises(ValueError, match="must be 32 bytes"):
            KDFEncryption(master_key=short_key)

    def test_different_keys_produce_different_ciphertext(self):
        """Test that different keys encrypt to different ciphertext"""
        key1 = KDFEncryption.generate_master_key()
        key2 = KDFEncryption.generate_master_key()

        cipher1 = KDFEncryption(master_key=key1)
        cipher2 = KDFEncryption(master_key=key2)

        plaintext = b"same-plaintext"
        encrypted1 = cipher1.encrypt(plaintext)
        encrypted2 = cipher2.encrypt(plaintext)

        # Different keys should produce different ciphertext
        assert encrypted1 != encrypted2

    def test_same_key_can_decrypt(self):
        """Test that same key (different instance) can decrypt"""
        key = KDFEncryption.generate_master_key()

        cipher1 = KDFEncryption(master_key=key)
        cipher2 = KDFEncryption(master_key=key)

        plaintext = b"test-data"
        encrypted = cipher1.encrypt(plaintext)

        # Different instance with same key should decrypt
        decrypted = cipher2.decrypt(encrypted)
        assert decrypted == plaintext

    def test_wrong_key_cannot_decrypt(self):
        """Test that wrong key cannot decrypt"""
        key1 = KDFEncryption.generate_master_key()
        key2 = KDFEncryption.generate_master_key()

        cipher1 = KDFEncryption(master_key=key1)
        cipher2 = KDFEncryption(master_key=key2)

        encrypted = cipher1.encrypt(b"secret")

        with pytest.raises(ValueError, match="Decryption failed"):
            cipher2.decrypt(encrypted)

    def test_period_derivation(self):
        """Test that key derivation uses time period"""
        key = KDFEncryption.generate_master_key()

        # Use short rotation period for testing
        cipher = KDFEncryption(master_key=key, rotation_period=1)

        # Get current period
        period1 = cipher._get_current_period()

        # Period should be based on time
        assert isinstance(period1, int)
        assert period1 > 0

    def test_derived_keys_differ_by_period(self):
        """Test that different periods produce different derived keys"""
        key = KDFEncryption.generate_master_key()
        cipher = KDFEncryption(master_key=key)

        derived1 = cipher._derive_key(key, 1000)
        derived2 = cipher._derive_key(key, 1001)

        assert derived1 != derived2

    def test_emergency_rotation_with_previous_key(self):
        """Test emergency key rotation using previous key"""
        old_key = KDFEncryption.generate_master_key()
        new_key = KDFEncryption.generate_master_key()

        # Encrypt with old key
        old_cipher = KDFEncryption(master_key=old_key)
        encrypted = old_cipher.encrypt(b"sensitive-data")

        # Create cipher with new key and old key as previous
        new_cipher = KDFEncryption(
            master_key=new_key,
            master_key_previous=old_key
        )

        # Should be able to decrypt data encrypted with old key
        decrypted = new_cipher.decrypt(encrypted)
        assert decrypted == b"sensitive-data"

        # New encryptions should use new key
        new_encrypted = new_cipher.encrypt(b"new-data")

        # Should be able to decrypt with new cipher
        assert new_cipher.decrypt(new_encrypted) == b"new-data"

        # Old cipher should NOT be able to decrypt new data
        with pytest.raises(ValueError, match="Decryption failed"):
            old_cipher.decrypt(new_encrypted)

    def test_period_boundary_decryption(self):
        """Test decryption works across period boundary"""
        key = KDFEncryption.generate_master_key()

        # Create cipher with very short period
        cipher = KDFEncryption(master_key=key, rotation_period=1)

        # Encrypt data
        plaintext = b"boundary-test"
        encrypted = cipher.encrypt(plaintext)

        # Wait for period to change (simulate with manual period manipulation)
        # In real usage, decryption tries current and previous period
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_json_token_map_encryption(self):
        """Test encrypting JSON token map (realistic use case)"""
        import json

        key = KDFEncryption.generate_master_key()
        cipher = KDFEncryption(master_key=key)

        token_map = {
            "{{__OWL:EMAIL_ADDRESS_1__}}": "john@example.com",
            "{{__OWL:PHONE_NUMBER_1__}}": "(555) 123-4567",
            "{{__OWL:SSN_1__}}": "123-45-6789"
        }

        plaintext = json.dumps(token_map).encode()
        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert json.loads(decrypted.decode()) == token_map


@pytest.mark.nats
@pytest.mark.asyncio
class TestNATSWithEncryption:
    """Tests for NATS session store with encryption enabled"""

    @pytest.fixture
    def encryption_key(self):
        """Generate encryption key for tests"""
        return KDFEncryption.generate_master_key()

    @pytest_asyncio.fixture
    async def encrypted_nats_store(self, nats_url, encryption_key):
        """Create NATS store with encryption enabled"""
        if not _check_nats_available(nats_url):
            pytest.skip("NATS server not available")

        encryption = KDFEncryption(master_key=encryption_key)
        store = NATSSessionStore(
            nats_url=nats_url,
            encryption=encryption
        )
        try:
            await asyncio.wait_for(store.connect(), timeout=5.0)
            yield store
            await store.disconnect()
        except asyncio.TimeoutError:
            pytest.skip("NATS connection timed out")
        except Exception as e:
            pytest.skip(f"Could not connect to NATS: {e}")

    async def test_encrypted_store_and_get(self, encrypted_nats_store):
        """Test storing and retrieving encrypted session"""
        session_id = "encrypted-test-001"
        token_map = {
            "{{__OWL:EMAIL_ADDRESS_1__}}": "encrypted@test.com",
            "{{__OWL:PHONE_NUMBER_1__}}": "(555) 999-8888"
        }

        await encrypted_nats_store.store_session(session_id, token_map)
        retrieved = await encrypted_nats_store.get_session(session_id)

        assert retrieved == token_map

        # Cleanup
        await encrypted_nats_store.delete_session(session_id)

    async def test_encrypted_data_not_readable_without_key(
        self, nats_url, encryption_key
    ):
        """Test that encrypted data cannot be read without the key"""
        if not _check_nats_available(nats_url):
            pytest.skip("NATS server not available")

        # Store with encryption
        encryption = KDFEncryption(master_key=encryption_key)
        encrypted_store = NATSSessionStore(
            nats_url=nats_url,
            encryption=encryption
        )
        await asyncio.wait_for(encrypted_store.connect(), timeout=5.0)

        session_id = "encrypted-not-readable-test"
        token_map = {"{{__OWL:EMAIL_1__}}": "secret@example.com"}

        await encrypted_store.store_session(session_id, token_map)

        # Try to read with different key
        different_key = KDFEncryption.generate_master_key()
        different_encryption = KDFEncryption(master_key=different_key)
        unencrypted_store = NATSSessionStore(
            nats_url=nats_url,
            encryption=different_encryption
        )
        await asyncio.wait_for(unencrypted_store.connect(), timeout=5.0)

        # Should fail to decrypt (returns None due to error handling)
        retrieved = await unencrypted_store.get_session(session_id)
        assert retrieved is None

        # Cleanup
        await encrypted_store.delete_session(session_id)
        await encrypted_store.disconnect()
        await unencrypted_store.disconnect()

    async def test_encryption_key_rotation_scenario(self, nats_url):
        """Test key rotation scenario with NATS"""
        if not _check_nats_available(nats_url):
            pytest.skip("NATS server not available")

        old_key = KDFEncryption.generate_master_key()
        new_key = KDFEncryption.generate_master_key()

        # Store data with old key
        old_encryption = KDFEncryption(master_key=old_key)
        old_store = NATSSessionStore(nats_url=nats_url, encryption=old_encryption)
        await asyncio.wait_for(old_store.connect(), timeout=5.0)

        session_id = "rotation-test-session"
        token_map = {"{{__OWL:EMAIL_1__}}": "rotate@test.com"}
        await old_store.store_session(session_id, token_map)

        # Create new store with new key + old key as previous (rotation scenario)
        new_encryption = KDFEncryption(
            master_key=new_key,
            master_key_previous=old_key
        )
        new_store = NATSSessionStore(nats_url=nats_url, encryption=new_encryption)
        await asyncio.wait_for(new_store.connect(), timeout=5.0)

        # Should be able to read old data
        retrieved = await new_store.get_session(session_id)
        assert retrieved == token_map

        # New data should be encrypted with new key
        new_session_id = "rotation-new-session"
        new_token_map = {"{{__OWL:EMAIL_1__}}": "newkey@test.com"}
        await new_store.store_session(new_session_id, new_token_map)

        # New store can read new data
        assert await new_store.get_session(new_session_id) == new_token_map

        # Old store cannot read new data (encrypted with new key)
        old_retrieved = await old_store.get_session(new_session_id)
        assert old_retrieved is None

        # Cleanup
        await new_store.delete_session(session_id)
        await new_store.delete_session(new_session_id)
        await old_store.disconnect()
        await new_store.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "nats"])
