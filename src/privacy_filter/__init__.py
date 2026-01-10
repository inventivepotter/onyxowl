"""
Privacy Filter - Reversible PII masking with GLiNER + Presidio

A privacy filter that uses GLiNER (zero-shot NER) and regex patterns
to detect and mask sensitive data, with reversible hash map-based de-masking.
"""

__version__ = "1.0.0"
__author__ = "Privacy Filter Team"

from .core import PrivacyFilter
from .models import (
    EntityType,
    MaskingResult,
    DemaskingResult,
    PiiMaskingStrategy,
)
from .gliner_engine import GLiNERPresidioEngine

__all__ = [
    "PrivacyFilter",
    "EntityType",
    "MaskingResult",
    "DemaskingResult",
    "PiiMaskingStrategy",
    "GLiNERPresidioEngine",
]
