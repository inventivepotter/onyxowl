"""
Data models and enums for Privacy Filter
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class EntityType(str, Enum):
    """Entity types for detection"""
    # Personal Info
    PERSON = "PERSON"
    EMAIL = "EMAIL_ADDRESS"
    PHONE = "PHONE_NUMBER"
    SSN = "US_SSN"

    # Financial
    CREDIT_CARD = "CREDIT_CARD"
    BITCOIN = "BITCOIN_ADDRESS"
    ETHEREUM = "ETHEREUM_ADDRESS"
    IBAN = "IBAN_CODE"

    # Secrets
    AWS_KEY = "AWS_ACCESS_KEY_ID"
    API_KEY = "API_KEY"
    PASSWORD = "PASSWORD"
    JWT = "JWT_TOKEN"

    # Location
    ADDRESS = "LOCATION"
    IP_ADDRESS = "IP_ADDRESS"

    # Health
    MEDICAL_LICENSE = "MEDICAL_LICENSE"


class PiiMaskingStrategy(str, Enum):
    """Masking strategies"""
    REPLACE = "REPLACE"           # {{__OWL:EMAIL_ADDRESS_1__}}
    FPE = "FPE"                   # Format-preserving encryption
    SYNTHETIC = "SYNTHETIC"        # Fake data
    REDACT = "REDACT"             # [REDACTED]
    TRUNCATE = "TRUNCATE"         # user@***.com
    HASH = "HASH"                 # SHA256 hash
    TOKENIZE = "TOKENIZE"         # Reversible token


@dataclass
class MaskingResult:
    """Result of masking operation"""
    masked_text: str
    token_map: Dict[str, str]  # masked_token -> original_value
    entities_found: List[Dict]
    session_id: str


@dataclass
class DemaskingResult:
    """Result of de-masking operation"""
    original_text: str
    entities_restored: int
