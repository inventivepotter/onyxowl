"""
NATS JetStream session storage for Privacy Filter.

Provides distributed session storage with automatic TTL expiration,
audit event publishing, and KDF-based encryption with automatic rotation.
"""

import base64
import json
import logging
import os
import time
from typing import Optional

import nats
from nats.js.api import KeyValueConfig
from nats.js.errors import KeyNotFoundError
from nats.js.kv import KeyValue

logger = logging.getLogger(__name__)

# ============================================================================
# KDF Encryption with Automatic 24-Hour Rotation
# ============================================================================

# Rotation period in seconds (24 hours)
KDF_ROTATION_PERIOD_SECONDS = 86400


class KDFEncryption:
    """
    KDF-based encryption with automatic 24-hour key rotation.

    Uses HKDF to derive time-based keys from a master key.
    Keys automatically rotate every 24 hours without manual intervention.

    For emergency rotation (key compromise), set ENCRYPTION_MASTER_KEY_PREVIOUS
    and wait for TTL expiration (15 min max), then remove the previous key.

    Security properties:
    - Automatic rotation: Derived keys change every 24 hours
    - Emergency rotation: Dual-key support during compromise recovery
    - Forward secrecy: NOT provided (master key derives all keys)

    Usage:
        cipher = KDFEncryption()
        if cipher.is_enabled:
            encrypted = cipher.encrypt(b"sensitive data")
            decrypted = cipher.decrypt(encrypted)
    """

    def __init__(
        self,
        master_key: Optional[str] = None,
        master_key_previous: Optional[str] = None,
        rotation_period: int = KDF_ROTATION_PERIOD_SECONDS,
    ):
        """
        Initialize KDF encryption.

        Args:
            master_key: Base64-encoded 32-byte master key (from env if not provided)
            master_key_previous: Previous master key for emergency rotation
            rotation_period: Key rotation period in seconds (default: 24 hours)
        """
        self._master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")
        self._master_key_previous = master_key_previous or os.getenv(
            "ENCRYPTION_MASTER_KEY_PREVIOUS"
        )
        self._rotation_period = rotation_period
        self._fernet_cache: dict[str, "Fernet"] = {}

        # Validate keys if provided
        if self._master_key:
            self._validate_key(self._master_key, "ENCRYPTION_MASTER_KEY")
        if self._master_key_previous:
            self._validate_key(self._master_key_previous, "ENCRYPTION_MASTER_KEY_PREVIOUS")

    @property
    def is_enabled(self) -> bool:
        """Check if encryption is enabled (master key is set)."""
        return self._master_key is not None

    @staticmethod
    def generate_master_key() -> str:
        """
        Generate a new master key for use in ENCRYPTION_MASTER_KEY.

        Returns:
            Base64-encoded 32-byte key suitable for .env file

        Example:
            python -c "from privacy_filter.nats_store import KDFEncryption; print(KDFEncryption.generate_master_key())"
        """
        import secrets
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

    def _validate_key(self, key: str, name: str) -> None:
        """Validate that a key is properly formatted."""
        try:
            decoded = base64.urlsafe_b64decode(key.encode())
            if len(decoded) != 32:
                raise ValueError(f"{name} must be 32 bytes when decoded")
        except Exception as e:
            raise ValueError(
                f"Invalid {name}: must be base64-encoded 32 bytes. "
                f"Generate with: KDFEncryption.generate_master_key(). Error: {e}"
            )

    def _get_current_period(self) -> int:
        """Get current rotation period (changes every 24 hours)."""
        return int(time.time() // self._rotation_period)

    def _derive_key(self, master_key: str, period: int) -> bytes:
        """
        Derive a Fernet key from master key and time period using HKDF.

        Args:
            master_key: Base64-encoded master key
            period: Time period (unix_time // rotation_period)

        Returns:
            32-byte derived key suitable for Fernet
        """
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes

        master_bytes = base64.urlsafe_b64decode(master_key.encode())

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=f"privacy-filter-session-key-period-{period}".encode(),
        )

        return base64.urlsafe_b64encode(hkdf.derive(master_bytes))

    def _get_fernet(self, master_key: str, period: int) -> "Fernet":
        """Get or create a Fernet instance for given master key and period."""
        from cryptography.fernet import Fernet

        cache_key = f"{master_key}:{period}"

        if cache_key not in self._fernet_cache:
            derived_key = self._derive_key(master_key, period)
            self._fernet_cache[cache_key] = Fernet(derived_key)

            # Limit cache size (keep only recent periods)
            if len(self._fernet_cache) > 10:
                # Remove oldest entries
                keys_to_remove = list(self._fernet_cache.keys())[:-5]
                for k in keys_to_remove:
                    del self._fernet_cache[k]

        return self._fernet_cache[cache_key]

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data using current period's derived key.

        Args:
            data: Plaintext bytes to encrypt

        Returns:
            Encrypted bytes (Fernet token)

        Raises:
            RuntimeError: If encryption is not enabled
        """
        if not self.is_enabled:
            raise RuntimeError(
                "Encryption not enabled. Set ENCRYPTION_MASTER_KEY environment variable."
            )

        period = self._get_current_period()
        fernet = self._get_fernet(self._master_key, period)

        return fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data, trying current and previous periods/keys.

        Attempts decryption in order:
        1. Current master key, current period
        2. Current master key, previous period (handles period boundary)
        3. Previous master key, current period (during emergency rotation)
        4. Previous master key, previous period (during emergency rotation)

        Args:
            data: Encrypted bytes (Fernet token)

        Returns:
            Decrypted plaintext bytes

        Raises:
            RuntimeError: If encryption is not enabled
            DecryptionError: If decryption fails with all keys/periods
        """
        from cryptography.fernet import InvalidToken

        if not self.is_enabled:
            raise RuntimeError(
                "Encryption not enabled. Set ENCRYPTION_MASTER_KEY environment variable."
            )

        current_period = self._get_current_period()
        previous_period = current_period - 1

        # Build list of (master_key, period) combinations to try
        attempts = [
            (self._master_key, current_period),
            (self._master_key, previous_period),
        ]

        # Add previous master key attempts if set (emergency rotation)
        if self._master_key_previous:
            attempts.extend([
                (self._master_key_previous, current_period),
                (self._master_key_previous, previous_period),
            ])

        last_error = None
        for master_key, period in attempts:
            try:
                fernet = self._get_fernet(master_key, period)
                return fernet.decrypt(data)
            except InvalidToken as e:
                last_error = e
                continue

        # All attempts failed
        raise ValueError(
            f"Decryption failed: data may be corrupted or encrypted with unknown key. "
            f"If you recently rotated keys, ensure ENCRYPTION_MASTER_KEY_PREVIOUS is set. "
            f"Last error: {last_error}"
        )


# Global encryption instance (initialized lazily)
_encryption: Optional[KDFEncryption] = None


def get_encryption() -> KDFEncryption:
    """Get or create the global KDF encryption instance."""
    global _encryption

    if _encryption is None:
        _encryption = KDFEncryption()

        if _encryption.is_enabled:
            logger.info(
                "KDF encryption enabled with 24-hour automatic rotation. "
                f"Previous key configured: {_encryption._master_key_previous is not None}"
            )
        else:
            logger.warning(
                "KDF encryption disabled. Set ENCRYPTION_MASTER_KEY to enable. "
                "Generate key with: python -c \"from privacy_filter.nats_store import KDFEncryption; print(KDFEncryption.generate_master_key())\""
            )

    return _encryption


# Error message constant
_NATS_NOT_CONNECTED_ERROR = "NATS not connected. Call connect() first."


class NATSSessionStore:
    """
    Session storage using NATS JetStream KV.

    Stores token mappings with automatic TTL expiration.
    Publishes audit events for observability.
    Optionally encrypts data using KDF-based encryption.
    """

    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        bucket_name: str = "privacy_sessions",
        ttl_seconds: int = 900,  # 15 minutes max (for key rotation)
        encryption: Optional[KDFEncryption] = None,
    ):
        self.nats_url = nats_url
        self.bucket_name = bucket_name
        self.ttl_seconds = ttl_seconds
        self._nc: Optional[nats.NATS] = None
        self._js = None
        self._kv: Optional[KeyValue] = None
        self._encryption = encryption or get_encryption()

    async def connect(self) -> None:
        """Initialize NATS connection and JetStream KV bucket."""
        self._nc = await nats.connect(self.nats_url)
        self._js = self._nc.jetstream()

        # Create or get KV bucket with TTL
        try:
            self._kv = await self._js.key_value(self.bucket_name)
            logger.info(f"Connected to existing KV bucket: {self.bucket_name}")
        except Exception:
            # Bucket doesn't exist, create it
            self._kv = await self._js.create_key_value(
                KeyValueConfig(
                    bucket=self.bucket_name,
                    ttl=self.ttl_seconds,
                    history=1,  # Only keep latest value
                    storage="memory",  # Use memory for speed
                )
            )
            logger.info(f"Created KV bucket: {self.bucket_name} with TTL: {self.ttl_seconds}s")

    async def disconnect(self) -> None:
        """Close NATS connection."""
        if self._nc:
            await self._nc.close()
            self._nc = None
            self._kv = None

    async def store_session(
        self,
        session_id: str,
        token_map: dict[str, str],
    ) -> None:
        """
        Store token mappings for a session.

        Data is encrypted if ENCRYPTION_MASTER_KEY is configured.

        Args:
            session_id: Unique session identifier
            token_map: Mapping of tokens to original values
                       e.g., {"<EMAIL_ADDRESS_1>": "john@example.com"}
        """
        if not self._kv:
            raise RuntimeError(_NATS_NOT_CONNECTED_ERROR)

        key = f"session:{session_id}"
        value = json.dumps(token_map).encode()

        # Encrypt if enabled
        if self._encryption.is_enabled:
            value = self._encryption.encrypt(value)

        await self._kv.put(key, value)

        # Publish audit event (fire-and-forget)
        await self._publish_event("mask", {
            "session_id": session_id,
            "token_count": len(token_map),
            "token_types": list({t.split("_")[0].strip("<") for t in token_map.keys()}),
            "encrypted": self._encryption.is_enabled,
        })

        logger.debug(
            f"Stored session {session_id} with {len(token_map)} tokens "
            f"(encrypted: {self._encryption.is_enabled})"
        )

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[dict[str, str]]:
        """
        Retrieve token mappings for a session.

        Data is decrypted if ENCRYPTION_MASTER_KEY is configured.

        Args:
            session_id: Unique session identifier

        Returns:
            Token map if found, None if expired or not found
        """
        if not self._kv:
            raise RuntimeError(_NATS_NOT_CONNECTED_ERROR)

        key = f"session:{session_id}"

        try:
            entry = await self._kv.get(key)
            value = entry.value

            # Decrypt if encryption is enabled
            if self._encryption.is_enabled:
                try:
                    value = self._encryption.decrypt(value)
                except ValueError as e:
                    logger.error(f"Decryption failed for session {session_id}: {e}")
                    return None

            token_map = json.loads(value.decode())
            logger.debug(f"Retrieved session {session_id}")
            return token_map
        except KeyNotFoundError:
            logger.warning(f"Session not found or expired: {session_id}")
            return None

    async def resolve_tokens(
        self,
        session_id: str,
        tokens: list[str],
    ) -> dict[str, str]:
        """
        Resolve specific tokens from a session.

        Called by agent frameworks before executing tools
        to get real values for masked tokens.

        Args:
            session_id: Unique session identifier
            tokens: List of tokens to resolve

        Returns:
            Mapping of tokens to original values
        """
        token_map = await self.get_session(session_id)

        if not token_map:
            logger.error(f"Cannot resolve tokens: session {session_id} not found")
            return {}

        resolved = {
            token: token_map.get(token, token)
            for token in tokens
        }

        # Publish audit event
        await self._publish_event("resolve", {
            "session_id": session_id,
            "tokens_requested": len(tokens),
            "tokens_resolved": sum(1 for t in tokens if t in token_map),
        })

        return resolved

    async def delete_session(self, session_id: str) -> bool:
        """
        Manually delete a session before TTL expiration.

        Args:
            session_id: Unique session identifier

        Returns:
            True if deleted, False if not found
        """
        if not self._kv:
            raise RuntimeError(_NATS_NOT_CONNECTED_ERROR)

        key = f"session:{session_id}"

        try:
            await self._kv.delete(key)
            await self._publish_event("delete", {"session_id": session_id})
            logger.info(f"Deleted session {session_id}")
            return True
        except KeyNotFoundError:
            return False

    async def extend_session(
        self,
        session_id: str,
        additional_tokens: dict[str, str],
    ) -> bool:
        """
        Add more tokens to an existing session.

        Useful for multi-turn conversations where new PII
        is detected in subsequent messages.

        Args:
            session_id: Unique session identifier
            additional_tokens: New tokens to add

        Returns:
            True if extended, False if session not found
        """
        existing = await self.get_session(session_id)

        if existing is None:
            return False

        # Merge token maps
        merged = {**existing, **additional_tokens}
        await self.store_session(session_id, merged)

        return True

    async def _publish_event(self, event_type: str, data: dict) -> None:
        """Publish audit event to NATS subject."""
        if not self._nc:
            return

        subject = f"privacy.events.{event_type}"
        payload = json.dumps(data).encode()

        try:
            await self._nc.publish(subject, payload)
        except Exception as e:
            # Don't fail main operation if event publishing fails
            logger.warning(f"Failed to publish event: {e}")


# Singleton instance for FastAPI
_store: Optional[NATSSessionStore] = None


async def get_nats_store() -> NATSSessionStore:
    """Get or create NATS session store singleton."""
    global _store

    if _store is None:
        _store = NATSSessionStore(
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "900")),
        )
        await _store.connect()

    return _store
