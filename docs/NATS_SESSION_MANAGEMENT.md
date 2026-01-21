# NATS for Session Storage & Token Resolution

This document describes how to integrate NATS JetStream for distributed session management and secure token resolution in the Privacy Filter.

## Why NATS over Redis?

| Feature | NATS JetStream | Redis |
|---------|----------------|-------|
| **Architecture** | Distributed by design | Requires clustering setup |
| **Latency** | Sub-millisecond | Sub-millisecond |
| **Pub/Sub** | Native, first-class | Supported but secondary |
| **Persistence** | Built-in with JetStream | RDB/AOF |
| **Memory footprint** | ~10-50MB | ~50-100MB |
| **TTL Support** | Yes (via KV buckets) | Yes |
| **Observability** | Built-in metrics | Requires setup |
| **Cloud-native** | K8s operator, Helm charts | Operator available |

**Key advantages for our use case**:
1. **Event-driven architecture**: Pub/sub for token resolution events
2. **Lightweight**: Lower memory footprint for edge deployments
3. **Built-in KV**: JetStream KV buckets with TTL for session storage
4. **Request-Reply**: Native pattern for synchronous token resolution

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Request                                    │
│                "Book flight to NYC on Feb 3rd"                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Privacy Filter API (POST /mask)                           │
│                                                                              │
│  1. Detect entities: "NYC" (LOCATION), "Feb 3rd" (DATE)                     │
│  2. Generate tokens: [LOC_a1b2], [DATE_c3d4]                                │
│  3. Store in NATS KV: session:{id} → token mappings                         │
│                                                                              │
│  Output: "Book flight to [LOC_a1b2] on [DATE_c3d4]"                         │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM Agent                                       │
│                                                                              │
│  Processes masked text, generates tool call:                                 │
│  book_flight(destination="[LOC_a1b2]", date="[DATE_c3d4]")                  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                Agent Framework (LangChain, CrewAI, etc.)                     │
│                                                                              │
│  Before executing tool, calls POST /resolve:                                 │
│  {"session_id": "abc-123", "tokens": ["[LOC_a1b2]", "[DATE_c3d4]"]}         │
│                                                                              │
│  Response: {"[LOC_a1b2]": "NYC", "[DATE_c3d4]": "Feb 3rd"}                  │
│                                                                              │
│  Then executes: book_flight(destination="NYC", date="Feb 3rd")              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          External Tool/API                                   │
│                       (Receives real values)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## NATS Components Used

### 1. JetStream KV Store (Session Storage)

Stores token mappings with automatic TTL expiration.

```
Bucket: privacy_sessions
├── session:abc-123 → {"[LOC_a1b2]": "NYC", "[DATE_c3d4]": "Feb 3rd"}
├── session:def-456 → {"[EMAIL_x9y8]": "user@example.com"}
└── session:ghi-789 → {...}

TTL: 15 minutes (configurable)
```

### 2. Pub/Sub (Audit Events)

Publishes events for audit logging without blocking main flow.

```
Subject: privacy.events.{event_type}
├── privacy.events.mask      → Token created
├── privacy.events.resolve   → Token resolved (at tool call)
├── privacy.events.expire    → Session expired
└── privacy.events.delete    → Session deleted
```

### 3. HTTP API (Synchronous Resolution)

Agent frameworks call `POST /resolve` before executing tools.

```
POST /resolve
Request:  {"session_id": "abc-123", "tokens": ["[LOC_a1b2]", "[DATE_c3d4]"]}
Response: {"resolved": {"[LOC_a1b2]": "NYC", "[DATE_c3d4]": "Feb 3rd"}}
```

## Installation

### 1. Add Dependencies

```bash
# Add to requirements.txt
nats-py>=2.6.0
```

Or install directly:
```bash
pip install nats-py
```

### 2. Docker Compose Setup

Add to `docker/docker-compose.yml`:

```yaml
services:
  privacy-filter:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "1001:1001"
    environment:
      - NATS_URL=nats://nats:4222
      - SESSION_TTL_SECONDS=900
    depends_on:
      nats:
        condition: service_healthy

  nats:
    image: nats:2.10-alpine
    ports:
      - "4222:4222"   # Client connections
      - "8222:8222"   # HTTP monitoring
    command: ["--jetstream", "--store_dir=/data", "-m", "8222"]
    volumes:
      - nats_data:/data
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8222/healthz"]
      interval: 5s
      timeout: 3s
      retries: 3

volumes:
  nats_data:
```

### 3. Production Docker Compose

Add to `docker/docker-compose.prod.yml`:

```yaml
services:
  nats:
    image: nats:2.10-alpine
    command:
      - "--jetstream"
      - "--store_dir=/data"
      - "--max_memory_store=1GB"
      - "--max_file_store=10GB"
      - "-m"
      - "8222"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 128M
    restart: unless-stopped
```

## Implementation

### 1. NATS Session Store

Create `src/privacy_filter/nats_store.py`:

```python
import asyncio
import json
import logging
from typing import Optional
from datetime import timedelta

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
                       e.g., {"[LOC_a1b2]": "NYC", "[DATE_c3d4]": "Feb 3rd"}
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
                t.split("_")[0].strip("[") for t in token_map.keys()
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
        import os
        _store = NATSSessionStore(
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "900")),
        )
        await _store.connect()

    return _store
```

### 2. FastAPI Integration

Update `api/main.py`:

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from privacy_filter import PrivacyFilter
from privacy_filter.nats_store import NATSSessionStore, get_nats_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage NATS connection lifecycle."""
    # Startup
    store = await get_nats_store()
    app.state.nats_store = store

    yield

    # Shutdown
    await store.disconnect()


app = FastAPI(
    title="Privacy Filter API",
    description="PII detection and masking with NATS session storage",
    lifespan=lifespan,
)

filter_instance = PrivacyFilter(use_gliner=True)


class MaskRequest(BaseModel):
    text: str
    entities_to_mask: list[str] | None = None


class MaskResponse(BaseModel):
    masked_text: str
    session_id: str
    entity_count: int


class DemaskRequest(BaseModel):
    masked_text: str
    session_id: str


class ResolveRequest(BaseModel):
    session_id: str
    tokens: list[str]


async def get_store() -> NATSSessionStore:
    """Dependency to get NATS store."""
    return await get_nats_store()


@app.post("/mask", response_model=MaskResponse)
async def mask_text(
    request: MaskRequest,
    store: NATSSessionStore = Depends(get_store),
):
    """
    Mask PII in text and store token mappings in NATS.

    Returns masked text and session_id for later de-masking.
    """
    result = filter_instance.mask(
        request.text,
        entities_to_mask=request.entities_to_mask,
    )

    # Store in NATS with TTL
    await store.store_session(result.session_id, result.token_map)

    return MaskResponse(
        masked_text=result.masked_text,
        session_id=result.session_id,
        entity_count=len(result.token_map),
    )


@app.post("/demask")
async def demask_text(
    request: DemaskRequest,
    store: NATSSessionStore = Depends(get_store),
):
    """
    Restore original values in masked text.

    Retrieves token mappings from NATS using session_id.
    """
    token_map = await store.get_session(request.session_id)

    if token_map is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found or expired: {request.session_id}",
        )

    # Replace tokens with original values
    original_text = request.masked_text
    for token, value in token_map.items():
        original_text = original_text.replace(token, value)

    return {"original_text": original_text}


@app.post("/resolve")
async def resolve_tokens(
    request: ResolveRequest,
    store: NATSSessionStore = Depends(get_store),
):
    """
    Resolve specific tokens from a session.

    Called by agent frameworks before executing tools.
    """
    resolved = await store.resolve_tokens(
        request.session_id,
        request.tokens,
    )

    if not resolved:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}",
        )

    return {"resolved": resolved}


@app.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    store: NATSSessionStore = Depends(get_store),
):
    """Manually delete a session before TTL expiration."""
    deleted = await store.delete_session(session_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}",
        )

    return {"deleted": True}


@app.get("/health")
async def health_check(store: NATSSessionStore = Depends(get_store)):
    """Health check including NATS connectivity."""
    try:
        # Simple KV operation to verify connectivity
        await store._kv.status()
        nats_status = "connected"
    except Exception as e:
        nats_status = f"error: {e}"

    return {
        "status": "healthy",
        "nats": nats_status,
    }
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NATS_URL` | `nats://localhost:4222` | NATS server URL |
| `SESSION_TTL_SECONDS` | `900` (15 min) | Session expiration time |
| `NATS_BUCKET_NAME` | `privacy_sessions` | KV bucket name |

### Recommended TTL Values

| Use Case | TTL | Rationale |
|----------|-----|-----------|
| Single request | 60s | Quick mask → LLM → demask |
| Multi-turn chat | 900s (15m) | Typical conversation length |
| Long workflows | 3600s (1hr) | Complex agent tasks |
| Debug/testing | 86400s (24hr) | Development convenience |

## Monitoring

### NATS Monitoring Endpoints

NATS exposes metrics at `http://localhost:8222`:

```bash
# Server info
curl http://localhost:8222/varz

# JetStream info
curl http://localhost:8222/jsz

# Connections
curl http://localhost:8222/connz
```

### Audit Event Consumer

Create a service to consume audit events:

```python
import asyncio
import nats


async def audit_consumer():
    """Consume and log privacy audit events."""
    nc = await nats.connect("nats://localhost:4222")

    async def handler(msg):
        print(f"Event: {msg.subject}")
        print(f"Data: {msg.data.decode()}")

    # Subscribe to all privacy events
    await nc.subscribe("privacy.events.*", cb=handler)

    # Keep running
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(audit_consumer())
```

### Prometheus Metrics (Optional)

Add to your FastAPI app:

```python
from prometheus_client import Counter, Histogram

MASK_COUNTER = Counter(
    "privacy_mask_total",
    "Total mask operations",
    ["entity_type"],
)

RESOLVE_LATENCY = Histogram(
    "privacy_resolve_seconds",
    "Token resolution latency",
)
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from privacy_filter.nats_store import NATSSessionStore


@pytest.fixture
async def mock_store():
    store = NATSSessionStore()
    store._nc = AsyncMock()
    store._kv = AsyncMock()
    return store


@pytest.mark.asyncio
async def test_store_session(mock_store):
    await mock_store.store_session(
        "test-session",
        {"[LOC_abc]": "NYC"},
    )

    mock_store._kv.put.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_tokens(mock_store):
    mock_store._kv.get.return_value = MagicMock(
        value=b'{"[LOC_abc]": "NYC"}'
    )

    resolved = await mock_store.resolve_tokens(
        "test-session",
        ["[LOC_abc]"],
    )

    assert resolved == {"[LOC_abc]": "NYC"}
```

### Integration Tests

```python
import pytest
import asyncio

from privacy_filter.nats_store import NATSSessionStore


@pytest.fixture
async def nats_store():
    """Real NATS connection for integration tests."""
    store = NATSSessionStore(
        nats_url="nats://localhost:4222",
        ttl_seconds=60,
    )
    await store.connect()
    yield store
    await store.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_session_lifecycle(nats_store):
    session_id = "test-session-123"
    token_map = {
        "[EMAIL_abc]": "user@example.com",
        "[PHONE_xyz]": "555-1234",
    }

    # Store
    await nats_store.store_session(session_id, token_map)

    # Retrieve
    retrieved = await nats_store.get_session(session_id)
    assert retrieved == token_map

    # Resolve specific tokens
    resolved = await nats_store.resolve_tokens(
        session_id,
        ["[EMAIL_abc]"],
    )
    assert resolved == {"[EMAIL_abc]": "user@example.com"}

    # Delete
    deleted = await nats_store.delete_session(session_id)
    assert deleted is True

    # Verify deleted
    retrieved = await nats_store.get_session(session_id)
    assert retrieved is None
```

## Security Considerations

### 1. Application-Level Encryption (KDF-based)

The Privacy Filter includes built-in KDF-based encryption with automatic 24-hour key rotation. This provides encryption at rest independent of NATS configuration.

#### How It Works

```
Master Key (ENCRYPTION_MASTER_KEY)
        │
        ▼
   ┌─────────────────────────────────────────┐
   │              HKDF Derivation            │
   │   derive(master_key, time_period)       │
   │   period = unix_time // 86400 (24hrs)   │
   └─────────────────────────────────────────┘
        │
        ▼
   Derived Key (changes every 24 hours)
        │
        ▼
   Fernet Encryption (AES-128-CBC + HMAC-SHA256)
        │
        ▼
   Encrypted Token Map → NATS KV Store
```

#### Enable Encryption

```bash
# Generate a master key
python -c "from privacy_filter.nats_store import KDFEncryption; print(KDFEncryption.generate_master_key())"

# Add to .env
ENCRYPTION_MASTER_KEY=your-generated-key-here
```

#### Automatic Rotation

- Derived keys rotate automatically every 24 hours
- No manual intervention required for routine rotation
- Decryption automatically tries current and previous period

#### Emergency Key Rotation (Compromise)

If the master key is compromised:

```bash
# 1. Generate new master key
python -c "from privacy_filter.nats_store import KDFEncryption; print(KDFEncryption.generate_master_key())"

# 2. Update .env - keep OLD key as PREVIOUS
ENCRYPTION_MASTER_KEY=new-key-here
ENCRYPTION_MASTER_KEY_PREVIOUS=old-compromised-key-here

# 3. Restart all instances
docker-compose restart

# 4. Wait 15 minutes (session TTL)
# All sessions encrypted with old key will expire naturally

# 5. Remove previous key from .env
ENCRYPTION_MASTER_KEY=new-key-here
# ENCRYPTION_MASTER_KEY_PREVIOUS=  (remove or comment out)

# 6. Restart all instances
docker-compose restart
```

#### Why 15-Minute TTL Matters

The maximum session TTL of 15 minutes enables simple key rotation:
- New sessions use new key
- Old sessions expire within 15 minutes
- No need to re-encrypt existing data
- Previous key only needed during transition window

#### Security Properties

| Property | Status | Notes |
|----------|--------|-------|
| Encryption at rest | ✅ Yes | AES-128-CBC via Fernet |
| Automatic rotation | ✅ Yes | Every 24 hours |
| Emergency rotation | ✅ Yes | Dual-key window (15 min) |
| Forward secrecy | ❌ No | Master key derives all keys |
| Key derivation | ✅ HKDF-SHA256 | ~5μs latency |

### 2. NATS-Level Encryption (Optional, Additional Layer)

For defense in depth, you can also enable NATS-level encryption:

```yaml
# nats-server.conf
jetstream {
  store_dir: /data
  cipher: aes  # Enable NATS encryption
  key: $NATS_ENCRYPTION_KEY
}
```

### 3. TLS in Transit

```yaml
# docker-compose.yml
nats:
  command:
    - "--jetstream"
    - "--tls"
    - "--tlscert=/certs/server.crt"
    - "--tlskey=/certs/server.key"
```

### 4. Authentication

```python
# Connect with credentials
nc = await nats.connect(
    "nats://localhost:4222",
    user="privacy_service",
    password=os.getenv("NATS_PASSWORD"),
)
```

### 5. Authorization

Use NATS accounts to isolate services:

```
# nats-server.conf
accounts {
  PRIVACY {
    users: [
      {user: privacy_service, password: $PASSWORD}
    ]
    jetstream: enabled
  }
}
```

### Compliance Summary

With KDF encryption enabled:

| Regulation | Encryption Requirement | Status |
|------------|------------------------|--------|
| GDPR | Encryption at rest | ✅ Met |
| GDPR | Breach notification exemption | ✅ Eligible (if key not compromised) |
| SOC 2 | Data encryption | ✅ Met |
| HIPAA | Encryption at rest | ✅ Met (but not true de-identification) |

## Migration from Redis

If migrating from Redis:

1. Run both stores in parallel during transition
2. Write to both, read from NATS
3. Monitor for issues
4. Remove Redis when confident

```python
class HybridStore:
    """Temporary dual-write store for migration."""

    def __init__(self, redis_store, nats_store):
        self.redis = redis_store
        self.nats = nats_store

    async def store_session(self, session_id, token_map):
        # Write to both
        await asyncio.gather(
            self.redis.store_session(session_id, token_map),
            self.nats.store_session(session_id, token_map),
        )

    async def get_session(self, session_id):
        # Read from NATS (primary)
        result = await self.nats.get_session(session_id)
        if result is None:
            # Fallback to Redis
            result = await self.redis.get_session(session_id)
        return result
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | NATS not running | Start NATS container |
| Session not found | TTL expired | Increase TTL or handle expiry |
| Slow resolution | Network latency | Use NATS cluster closer to app |
| Memory growth | Too many sessions | Reduce TTL, add monitoring |

### Debug Commands

```bash
# Check NATS is running
docker logs nats

# View JetStream streams
nats stream ls

# View KV buckets
nats kv ls

# Watch bucket activity
nats kv watch privacy_sessions
```

## References

- [NATS Documentation](https://docs.nats.io/)
- [NATS JetStream](https://docs.nats.io/nats-concepts/jetstream)
- [NATS Key-Value Store](https://docs.nats.io/nats-concepts/jetstream/key-value-store)
- [nats-py Client](https://github.com/nats-io/nats.py)
