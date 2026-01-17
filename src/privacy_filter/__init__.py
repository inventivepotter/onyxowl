"""
Privacy Filter - Reversible PII masking with GLiNER + Presidio

A privacy filter that uses GLiNER (zero-shot NER) and regex patterns
to detect and mask sensitive data, with reversible hash map-based de-masking.

Supports NATS JetStream for distributed session storage with automatic TTL.
"""

__version__ = "2.0.0"
__author__ = "Privacy Filter Team"

from .core import PrivacyFilter
from .models import (
    EntityType,
    MaskingResult,
    DemaskingResult,
    PiiMaskingStrategy,
)
from .gliner_engine import GLiNERPresidioEngine

# Optional NATS support
try:
    from .nats_store import NATSSessionStore, get_nats_store
    _NATS_AVAILABLE = True
except ImportError:
    NATSSessionStore = None
    get_nats_store = None
    _NATS_AVAILABLE = False

__all__ = [
    "PrivacyFilter",
    "EntityType",
    "MaskingResult",
    "DemaskingResult",
    "PiiMaskingStrategy",
    "GLiNERPresidioEngine",
    "NATSSessionStore",
    "get_nats_store",
]
