"""
NATS JetStream session storage for Privacy Filter.

Provides distributed session storage with automatic TTL expiration
and audit event publishing.
"""

import json
import logging
import os
from datetime import timedelta
from typing import Optional

import nats
from nats.js.api import KeyValueConfig
from nats.js.errors import KeyNotFoundError
from nats.js.kv import KeyValue

logger = logging.getLogger(__name__)


class NATSSessionStore:
    """
    Session storage using NATS JetStream KV.

    Stores token mappings with automatic TTL expiration.
    Publishes audit events for observability.
    """

    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        bucket_name: str = "privacy_sessions",
        ttl_seconds: int = 900,  # 15 minutes
    ):
        self.nats_url = nats_url
        self.bucket_name = bucket_name
        self.ttl = timedelta(seconds=ttl_seconds)
        self._nc: Optional[nats.NATS] = None
        self._js = None
        self._kv: Optional[KeyValue] = None

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
                    ttl=self.ttl,
                    history=1,  # Only keep latest value
                    storage="memory",  # Use memory for speed
                )
            )
            logger.info(f"Created KV bucket: {self.bucket_name} with TTL: {self.ttl}")

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

        Args:
            session_id: Unique session identifier
            token_map: Mapping of tokens to original values
                       e.g., {"<EMAIL_ADDRESS_1>": "john@example.com"}
        """
        if not self._kv:
            raise RuntimeError("NATS not connected. Call connect() first.")

        key = f"session:{session_id}"
        value = json.dumps(token_map)

        await self._kv.put(key, value.encode())

        # Publish audit event (fire-and-forget)
        await self._publish_event("mask", {
            "session_id": session_id,
            "token_count": len(token_map),
            "token_types": list(set(
                t.split("_")[0].strip("<") for t in token_map.keys()
            )),
        })

        logger.debug(f"Stored session {session_id} with {len(token_map)} tokens")

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[dict[str, str]]:
        """
        Retrieve token mappings for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            Token map if found, None if expired or not found
        """
        if not self._kv:
            raise RuntimeError("NATS not connected. Call connect() first.")

        key = f"session:{session_id}"

        try:
            entry = await self._kv.get(key)
            token_map = json.loads(entry.value.decode())
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
            raise RuntimeError("NATS not connected. Call connect() first.")

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
