"""
Regex patterns for PII detection
Comprehensive patterns for global coverage
"""

import re
from typing import Dict, List, Tuple

# ============================================================================
# Email Patterns
# ============================================================================

EMAIL_PATTERNS = {
    "standard": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "unicode": r'(?:^|(?<=\s))[\w.%+-]+@[\w.-]+\.[\w]{2,}(?=\s|$|[^\w.-])',  # Full Unicode support
    "unicode_simple": r'[A-Za-z0-9._%+-]+@[\w\-\.]+\.[A-Za-z\u0080-\uFFFF]{2,}',  # Unicode TLDs and domains
    "unicode_domain": r'[A-Za-z0-9._%+-]+@[^\s@]+\.[A-Za-z]{2,}',  # Permissive for Unicode domains
    "quoted": r'"[^"]+"|\'[^\']+\'@[\w.-]+\.[\w]{2,}',  # Quoted local parts
}

# ============================================================================
# Phone Number Patterns (Multi-Country)
# ============================================================================

PHONE_PATTERNS = {
    # North America (US, Canada)
    "us_standard": r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    "us_international": r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',

    # UK
    "uk_landline": r'\b0\d{2,4}[-.\s]?\d{6,8}\b',
    "uk_mobile": r'\b07\d{3}[-.\s]?\d{6}\b',
    "uk_international": r'\+44[-.\s]?\d{2,4}[-.\s]?\d{6,8}\b',

    # India
    "india_mobile": r'\b[6-9]\d{9}\b',
    "india_landline": r'\b0\d{2,4}[-.\s]?\d{6,8}\b',
    "india_international": r'\+91[-.\s]?[6-9]\d{9}\b',

    # Australia
    "australia_mobile": r'\b04\d{2}[-.\s]?\d{3}[-.\s]?\d{3}\b',
    "australia_landline": r'\b0[2-8][-.\s]?\d{4}[-.\s]?\d{4}\b',
    "australia_international": r'\+61[-.\s]?[2-478][-.\s]?\d{4}[-.\s]?\d{4}\b',

    # Germany
    "germany": r'\b0\d{2,5}[-.\s/]?\d{3,9}\b',
    "germany_international": r'\+49[-.\s]?\d{2,5}[-.\s/]?\d{3,9}\b',

    # France
    "france": r'\b0[1-9][-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}\b',
    "france_international": r'\+33[-.\s]?[1-9][-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}\b',

    # Japan
    "japan": r'\b0\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{4}\b',
    "japan_international": r'\+81[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{4}\b',

    # China
    "china_mobile": r'\b1[3-9]\d{9}\b',
    "china_landline": r'\b0\d{2,3}[-.\s]?\d{7,8}\b',
    "china_international": r'\+86[-.\s]?1[3-9]\d{9}\b',

    # Brazil
    "brazil_mobile": r'\b\(?\d{2}\)?[-.\s]?9[-.\s]?\d{4}[-.\s]?\d{4}\b',
    "brazil_landline": r'\b\(?\d{2}\)?[-.\s]?\d{4}[-.\s]?\d{4}\b',
    "brazil_international": r'\+55[-.\s]?\(?\d{2}\)?[-.\s]?9?[-.\s]?\d{4}[-.\s]?\d{4}\b',

    # Mexico
    "mexico": r'\b\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b',
    "mexico_international": r'\+52[-.\s]?\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}\b',

    # South Korea
    "korea_mobile": r'\b01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}\b',
    "korea_landline": r'\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b',
    "korea_international": r'\+82[-.\s]?1[016789][-.\s]?\d{3,4}[-.\s]?\d{4}\b',

    # Generic International
    "international": r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b',
}

# ============================================================================
# Credit Card Patterns
# ============================================================================

CREDIT_CARD_PATTERNS = {
    # Visa: Starts with 4, 13 or 16 digits
    "visa_13": r'\b4\d{12}\b',
    "visa_16": r'\b4\d{15}\b',
    "visa_spaced": r'\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',

    # Mastercard: Starts with 51-55 or 2221-2720, 16 digits
    "mastercard": r'\b5[1-5]\d{14}\b',
    "mastercard_2series": r'\b2(?:22[1-9]|2[3-9]\d|[3-6]\d{2}|7[01]\d|720)\d{12}\b',
    "mastercard_spaced": r'\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',

    # American Express: Starts with 34 or 37, 15 digits
    "amex": r'\b3[47]\d{13}\b',
    "amex_spaced": r'\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b',

    # Discover: Starts with 6011, 622126-622925, 644-649, 65, 16 digits
    "discover": r'\b6(?:011|5\d{2}|4[4-9]\d|22(?:1(?:2[6-9]|[3-9]\d)|[2-8]\d{2}|9(?:[01]\d|2[0-5])))\d{12}\b',
    "discover_spaced": r'\b6011[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',

    # Diners Club: Starts with 300-305, 36, 38, 14 digits
    "diners": r'\b3(?:0[0-5]|[68]\d)\d{11}\b',
    "diners_spaced": r'\b3(?:0[0-5]|[68]\d)[-\s]?\d{6}[-\s]?\d{4}\b',

    # JCB: Starts with 3528-3589, 16 digits
    "jcb": r'\b35(?:2[89]|[3-8]\d)\d{12}\b',
    "jcb_spaced": r'\b35(?:2[89]|[3-8]\d)[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',

    # Maestro: Starts with 50, 56-69, 12-19 digits
    "maestro": r'\b(?:5[06789]|6\d)\d{10,17}\b',

    # UnionPay: Starts with 62, 16-19 digits
    "unionpay": r'\b62\d{14,17}\b',

    # Generic (fallback)
    "generic": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
}

# ============================================================================
# SSN and National ID Patterns
# ============================================================================

SSN_PATTERNS = {
    # US SSN
    "us_ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "us_ssn_nospace": r'\b\d{9}\b',

    # UK National Insurance Number
    "uk_nino": r'\b[A-Z]{2}\s?\d{6}\s?[A-D]\b',

    # Canadian SIN
    "canada_sin": r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b',

    # Australian Tax File Number
    "australia_tfn": r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b',

    # German Tax ID
    "germany_tax": r'\b\d{11}\b',

    # French INSEE
    "france_insee": r'\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b',

    # Indian Aadhaar
    "india_aadhaar": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
}

# ============================================================================
# Cryptocurrency Addresses
# ============================================================================

CRYPTO_PATTERNS = {
    # Bitcoin (Legacy P2PKH)
    "bitcoin_p2pkh": r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',

    # Bitcoin (SegWit Bech32)
    "bitcoin_bech32": r'\bbc1[a-z0-9]{39,59}\b',

    # Ethereum
    "ethereum": r'\b0x[a-fA-F0-9]{40}\b',

    # Litecoin
    "litecoin": r'\b[LM][a-km-zA-HJ-NP-Z1-9]{26,33}\b',

    # Dogecoin
    "dogecoin": r'\bD[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}\b',

    # Ripple (XRP)
    "ripple": r'\br[a-zA-Z0-9]{24,34}\b',

    # Bitcoin Cash
    "bitcoin_cash": r'\b[13][a-km-zA-HJ-NP-Z1-9]{33}\b',

    # Monero
    "monero": r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b',
}

# ============================================================================
# API Keys and Secrets
# ============================================================================

API_KEY_PATTERNS = {
    # AWS
    "aws_access_key": r'\bAKIA[0-9A-Z]{16}\b',
    "aws_secret_key": r'\b[0-9a-zA-Z/+=]{40}\b',

    # Google API
    "google_api": r'\bAIza[0-9A-Za-z\-_]{35}\b',

    # GitHub
    "github_token": r'\bghp_[0-9a-zA-Z]{36}\b',
    "github_oauth": r'\bgho_[0-9a-zA-Z]{36}\b',

    # Stripe
    "stripe_live": r'\bsk_live_[0-9a-zA-Z]{24}\b',
    "stripe_test": r'\bsk_test_[0-9a-zA-Z]{24}\b',

    # OpenAI
    "openai": r'\bsk-[a-zA-Z0-9]{48}\b',

    # Azure
    "azure": r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',

    # JWT
    "jwt": r'\beyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*\b',

    # Generic API Key
    "generic_api_key": r'\b[a-zA-Z0-9]{32,}\b',
}

# ============================================================================
# IP Addresses
# ============================================================================

IP_PATTERNS = {
    # IPv4
    "ipv4": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',

    # IPv6
    "ipv6": r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
    "ipv6_compressed": r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b',
}

# ============================================================================
# IBAN (International Bank Account Number)
# ============================================================================

IBAN_PATTERNS = {
    # Generic IBAN
    "iban": r'\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b',

    # Country-specific IBANs
    "iban_de": r'\bDE\d{20}\b',  # Germany
    "iban_gb": r'\bGB\d{2}[A-Z]{4}\d{14}\b',  # UK
    "iban_fr": r'\bFR\d{12}[A-Z0-9]{11}\d{2}\b',  # France
    "iban_it": r'\bIT\d{2}[A-Z]\d{10}[A-Z0-9]{12}\b',  # Italy
    "iban_es": r'\bES\d{22}\b',  # Spain
}

# ============================================================================
# MAC Addresses
# ============================================================================

MAC_PATTERNS = {
    "mac_colon": r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b',
    "mac_dash": r'\b([0-9A-Fa-f]{2}-){5}([0-9A-Fa-f]{2})\b',
    "mac_dot": r'\b([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})\b',
}

# ============================================================================
# Driver's License Patterns (US States)
# ============================================================================

DRIVERS_LICENSE_PATTERNS = {
    "california": r'\b[A-Z]\d{7}\b',
    "florida": r'\b[A-Z]\d{12}\b',
    "texas": r'\b\d{8}\b',
    "new_york": r'\b\d{9}\b',
}

# ============================================================================
# Passport Numbers
# ============================================================================

PASSPORT_PATTERNS = {
    "us_passport": r'\b\d{9}\b',
    "uk_passport": r'\b\d{9}[A-Z]\b',
    "generic": r'\b[A-Z0-9]{6,9}\b',
}


def compile_all_patterns() -> Dict[str, List[Tuple[re.Pattern, str]]]:
    """
    Compile all regex patterns for efficient matching

    Returns:
        Dict mapping entity type to list of (compiled_pattern, pattern_name) tuples
    """
    compiled = {}

    # Email (with UNICODE flag for international characters)
    compiled["EMAIL_ADDRESS"] = [
        (re.compile(pattern, re.UNICODE | re.IGNORECASE), name)
        for name, pattern in EMAIL_PATTERNS.items()
    ]

    # Phone
    compiled["PHONE_NUMBER"] = [
        (re.compile(pattern), name)
        for name, pattern in PHONE_PATTERNS.items()
    ]

    # Credit Cards
    compiled["CREDIT_CARD"] = [
        (re.compile(pattern), name)
        for name, pattern in CREDIT_CARD_PATTERNS.items()
    ]

    # SSN
    compiled["US_SSN"] = [
        (re.compile(pattern), name)
        for name, pattern in SSN_PATTERNS.items()
    ]

    # Cryptocurrency
    compiled["CRYPTO_ADDRESS"] = [
        (re.compile(pattern), name)
        for name, pattern in CRYPTO_PATTERNS.items()
    ]

    # API Keys
    compiled["API_KEY"] = [
        (re.compile(pattern), name)
        for name, pattern in API_KEY_PATTERNS.items()
    ]

    # IP Addresses
    compiled["IP_ADDRESS"] = [
        (re.compile(pattern), name)
        for name, pattern in IP_PATTERNS.items()
    ]

    # IBAN
    compiled["IBAN_CODE"] = [
        (re.compile(pattern), name)
        for name, pattern in IBAN_PATTERNS.items()
    ]

    # MAC Address
    compiled["MAC_ADDRESS"] = [
        (re.compile(pattern), name)
        for name, pattern in MAC_PATTERNS.items()
    ]

    return compiled
