# Privacy Filter Guardrail Implementation Plan

## Executive Summary

**Goal:** Create a privacy filter guardrail for LLM prompt filtering using MCP (Model Context Protocol) that obfuscates PII, financial info, identifiable info, secrets/passwords, and other sensitive data.

**Recommendation:** Enhance the existing Presidio guardrail in the LiteLLM codebase (Python-based) rather than building a standalone Rust solution. This leverages mature infrastructure while adding advanced detection capabilities.

**Timeline:** 6 weeks for production-ready implementation

## Architecture Decision

### Recommended Approach: Enhanced Presidio Guardrail (Python)

**Why Python over Rust:**
- LiteLLM is 100% Python - no Rust code exists in codebase
- Existing Presidio guardrail already handles 40+ PII types with masking, async processing, and streaming
- Python ecosystem provides better ML/NER integration (spaCy, transformers)
- Faster time-to-market (6 weeks vs 12+ weeks for Rust)
- PyO3 bindings add complexity and maintenance burden

**When to Consider Rust Later:**
- After measuring performance bottlenecks (if latency >100ms)
- Processing millions of requests/second
- Standalone CLI tool distribution

## Proposed Solution: Dual-Track Implementation

### Track 1: Enhanced Presidio Guardrail (Primary - Production Ready)

**Location:** `/litellm/proxy/guardrails/guardrail_hooks/presidio.py`

**New Detection Capabilities (30+ new entity types):**

1. **Financial Patterns (regex-based)**
   - Bank account numbers (IBAN, SWIFT, US routing numbers)
   - Cryptocurrency addresses (Bitcoin, Ethereum, wallet addresses)
   - Payment card data (track data, CVV, expiry dates)
   - Tax IDs and financial identifiers

2. **Secret Patterns (integrate with existing secret detection)**
   - API keys/tokens (AWS, Azure, OpenAI, GitHub, etc.)
   - Private keys (SSH, RSA, PGP, TLS certificates)
   - Database connection strings
   - OAuth tokens and JWTs
   - Session tokens and cookies

3. **Biometric/Health Data (hybrid NER + regex)**
   - Medical record numbers
   - Health insurance identifiers
   - Prescription numbers
   - Lab result identifiers
   - DNA sequences
   - Biometric hashes

4. **Device/Network Identifiers**
   - MAC addresses
   - IMEI numbers
   - Device IDs
   - Geographic coordinates
   - IP addresses (already supported, enhanced)

**Enhanced Masking Strategies:**
- **REPLACE:** `<EMAIL_ADDRESS>` (existing)
- **FPE:** Format-preserving encryption using pyffx
- **SYNTHETIC:** Generate realistic fake data using faker
- **REDACT:** `[REDACTED - EMAIL]`
- **TRUNCATE:** `user@***.com`
- **HASH:** SHA256 hash
- **TOKENIZE:** Reversible token for unmasking

### Track 2: MCP Privacy Tools (Secondary - Experimental)

**Location:** `/litellm/proxy/_experimental/mcp_server/tools/privacy_tools.py`

**MCP Tools to Create:**
- `analyze_privacy_risk` - Analyze text for privacy risks without modification
- `mask_sensitive_data` - Apply privacy filters with various strategies
- `validate_compliance` - Check GDPR/CCPA/HIPAA compliance
- `generate_privacy_report` - Generate audit trail

**Why MCP:**
- Enable LLMs to request privacy analysis as tool calls
- Support privacy-aware agent workflows
- Provide REST API for external integrations

## Technical Specifications

### New PII Entity Types (70+ total)

```python
class PiiEntityType(str, Enum):
    # Existing 40+ types preserved (EMAIL, PHONE, PERSON, SSN, etc.)

    # Financial - Bank/Account
    IBAN_FULL = "IBAN_FULL"
    SWIFT_BIC = "SWIFT_BIC"
    US_ROUTING_NUMBER = "US_ROUTING_NUMBER"
    US_ACCOUNT_NUMBER = "US_ACCOUNT_NUMBER"

    # Financial - Crypto
    BITCOIN_ADDRESS = "BITCOIN_ADDRESS"
    ETHEREUM_ADDRESS = "ETHEREUM_ADDRESS"
    CRYPTO_WALLET = "CRYPTO_WALLET"

    # Financial - Payment
    CARD_TRACK_DATA = "CARD_TRACK_DATA"
    CVV = "CVV"
    CARD_EXPIRY = "CARD_EXPIRY"

    # Secrets/Credentials
    AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
    AWS_SECRET_KEY = "AWS_SECRET_KEY"
    AZURE_STORAGE_KEY = "AZURE_STORAGE_KEY"
    OPENAI_API_KEY = "OPENAI_API_KEY"
    GITHUB_TOKEN = "GITHUB_TOKEN"
    SSH_PRIVATE_KEY = "SSH_PRIVATE_KEY"
    DATABASE_CONNECTION_STRING = "DATABASE_CONNECTION_STRING"
    JWT_TOKEN = "JWT_TOKEN"
    OAUTH_TOKEN = "OAUTH_TOKEN"

    # Biometric/Health
    MEDICAL_RECORD_NUMBER = "MEDICAL_RECORD_NUMBER"
    HEALTH_INSURANCE_ID = "HEALTH_INSURANCE_ID"
    PRESCRIPTION_NUMBER = "PRESCRIPTION_NUMBER"
    DNA_SEQUENCE = "DNA_SEQUENCE"

    # Device/Network
    MAC_ADDRESS = "MAC_ADDRESS"
    IMEI = "IMEI"
    DEVICE_ID = "DEVICE_ID"
    GEO_COORDINATES = "GEO_COORDINATES"
    SESSION_TOKEN = "SESSION_TOKEN"
```

### Detection Methods

**1. High-Performance Regex Patterns**

```python
PATTERNS = {
    "BITCOIN_ADDRESS": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    "ETHEREUM_ADDRESS": r"\b0x[a-fA-F0-9]{40}\b",
    "AWS_ACCESS_KEY": r"AKIA[0-9A-Z]{16}",
    "MAC_ADDRESS": r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})",
    "JWT_TOKEN": r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*",
}
```

**2. Hybrid Approach (Regex + ML)**
- Fast regex scan (1-2ms)
- ML-based context validation (5-10ms)
- Pattern validation (checksums, Luhn algorithm)

**3. SpaCy NER Models**
- Use for contextual PII detection
- Fine-tune on privacy-specific corpus

### Masking Strategy Implementation

```python
class PiiMaskingStrategy(str, Enum):
    REPLACE = "REPLACE"
    FPE = "FPE"
    SYNTHETIC = "SYNTHETIC"
    REDACT = "REDACT"
    TRUNCATE = "TRUNCATE"
    HASH = "HASH"
    TOKENIZE = "TOKENIZE"
```

**Example Configuration:**

```yaml
guardrails:
  - guardrail_name: "privacy-filter-comprehensive"
    litellm_params:
      guardrail: presidio

      pii_entities_config:
        CREDIT_CARD: BLOCK
        BITCOIN_ADDRESS: MASK
        AWS_ACCESS_KEY: BLOCK
        EMAIL_ADDRESS: MASK
        PERSON: MASK

      masking_strategies:
        EMAIL_ADDRESS: TRUNCATE
        PHONE_NUMBER: FPE
        CREDIT_CARD: REDACT
        PERSON: SYNTHETIC
```

## Compliance Framework

### Compliance Profiles:
- **GDPR** - EU General Data Protection Regulation
- **CCPA** - California Consumer Privacy Act
- **HIPAA** - Health Insurance Portability and Accountability Act
- **PCI_DSS** - Payment Card Industry Data Security Standard
- **SOX** - Sarbanes-Oxley Act
- **FERPA** - Family Educational Rights and Privacy Act

### Compliance Validator:

```python
class ComplianceValidator:
    def validate_compliance(
        text: str,
        profile: ComplianceProfile,
        detected_entities: List[Entity]
    ) -> Dict:
        return {
            "compliant": bool,
            "profile": str,
            "violations": List[Dict],
            "risk_score": float,
            "remediation": str
        }
```

## Performance Targets

### Latency Targets:
- **p50:** <15ms per message (regex + validation)
- **p95:** <35ms per message (with ML validation)
- **p99:** <50ms per message (worst case)

### Throughput Targets:
- **Single instance:** 1,000 requests/second
- **With caching:** 10,000 requests/second
- **Horizontal scaling:** Linear with instances

### Optimization Strategies:
- **Regex compilation cache** - Pre-compile patterns
- **Async batching** - Process multiple texts in parallel
- **Result caching** - Cache analysis for 5 minutes
- **Lazy loading** - Load ML models only when needed
- **Progressive detection** - Regex → validation → ML (only if needed)

## Implementation Roadmap

### Phase 1: Enhanced Presidio (Weeks 1-3)

**Week 1: Detection Enhancement**
- Add 30+ new entity types to PiiEntityType enum
- Implement regex patterns for financial/crypto/secrets
- Create custom Presidio recognizers
- Unit tests for detection accuracy

**Week 2: Masking Strategies**
- Implement PiiMaskingStrategy enum
- Add FPE using pyffx library
- Implement synthetic data generation with faker
- Add truncation and redaction strategies
- Unit tests for each strategy

**Week 3: Compliance Framework**
- Create ComplianceProfile enum
- Implement compliance validators for GDPR/CCPA/HIPAA
- Add risk scoring algorithm
- Create audit trail logging
- Integration tests

**Deliverables:**
- Enhanced Presidio with 70+ entity types
- 7 masking strategies operational
- Compliance validation working
- Test coverage >85%

### Phase 2: MCP Tools Integration (Weeks 4-5)

**Week 4: MCP Tool Development**
- Create privacy_tools.py in MCP server
- Implement 4 core MCP tools
- Add tool registration
- REST API endpoints

**Week 5: Integration & Testing**
- Test MCP tools with Claude Desktop
- Integration with existing MCP server
- Documentation and examples
- Performance optimization

**Deliverables:**
- 4 MCP privacy tools operational
- REST API for external access
- Integration documentation

### Phase 3: Production Readiness (Week 6)

**Week 6: Production Hardening**
- Performance profiling and optimization
- Load testing (1,000+ req/sec target)
- Security audit
- Production deployment guide
- Monitoring dashboards

**Deliverables:**
- Performance benchmarks documented
- Production deployment guide
- Monitoring and alerting setup
- Security audit report

### Phase 4: Rust Evaluation (Optional - Weeks 7-8)

**Only if performance targets not met:**
- Build Rust proof-of-concept for regex engine
- PyO3 bindings for Python integration
- Performance comparison
- Go/no-go decision

## Technology Stack

### Core Libraries (Python):
- **Presidio** - PII detection framework (existing)
- **spaCy v3.7+** - NER models
- **regex** - Advanced pattern matching
- **pyffx** - Format-preserving encryption
- **faker** - Synthetic data generation
- **cryptography** - Hashing and encryption
- **pydantic v2** - Data validation (existing)
- **httpx** - Async HTTP client (existing)

### Development Tools:
- **pytest** - Testing framework (existing)
- **pytest-asyncio** - Async test support
- **pytest-benchmark** - Performance testing
- **black** - Code formatting (existing)
- **mypy** - Type checking (existing)

## Critical Files to Modify

### 1. `/litellm/proxy/guardrails/guardrail_hooks/presidio.py` (682 lines)
**Changes:**
- Add 30+ new entity types
- Implement new masking strategies
- Add compliance validation
- Enhance detection logic

### 2. `/litellm/types/guardrails.py` (548 lines)
**Changes:**
- Extend PiiEntityType enum
- Add PiiMaskingStrategy enum
- Add ComplianceProfile enum
- Update configuration models

### 3. `/litellm/proxy/guardrails/guardrail_initializers.py`
**Changes:**
- Update initialize_presidio() for new parameters
- Add compliance profile initialization
- Configure masking strategies

### 4. `/litellm/proxy/_experimental/mcp_server/server.py`
**Changes:**
- Register new privacy tools
- Add REST endpoints
- Integrate with guardrail registry

### 5. `/litellm/integrations/custom_guardrail.py`
**Changes:**
- Add compliance validation helpers
- Extend logging for masking strategies
- Add pre/post masking hooks

## Testing Strategy

### 1. Unit Tests

```python
def test_bitcoin_address_detection():
    text = "Send to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    results = detect_entities(text)
    assert any(r.entity_type == "BITCOIN_ADDRESS" for r in results)

def test_aws_key_detection():
    text = "AWS key: AKIAIOSFODNN7EXAMPLE"
    results = detect_entities(text)
    assert any(r.entity_type == "AWS_ACCESS_KEY" for r in results)
```

### 2. Integration Tests

```python
async def test_pre_call_hook_blocking():
    request = {"messages": [{"role": "user", "content": "SSN: 123-45-6789"}]}
    with pytest.raises(BlockedPiiEntityError):
        await guardrail.async_pre_call_hook(data=request)
```

### 3. Performance Tests

```python
def test_throughput():
    texts = ["Sample text with PII" * 10 for _ in range(1000)]
    results = asyncio.run(analyze_batch(texts))
    assert throughput > 500  # >500 req/sec
```

### 4. Compliance Tests

```python
def test_gdpr_compliance():
    text = "John Doe, email: john@example.com, IP: 192.168.1.1"
    report = validate_compliance(text, ComplianceProfile.GDPR)
    assert not report["compliant"]
    assert len(report["violations"]) >= 2
```

## Success Metrics

### Detection Quality:
- **Precision:** >95% (few false positives)
- **Recall:** >90% (catches most PII)
- **F1 Score:** >92% overall

### Performance:
- **Latency:** p95 <35ms per message
- **Throughput:** >1,000 req/sec single instance
- **Error Rate:** <0.1%

### Adoption:
- **Usage:** 50%+ of LiteLLM users enable privacy filter
- **Satisfaction:** 4.5+ stars
- **Issues:** <5 bug reports per month

### Compliance:
- **Coverage:** 100% of GDPR/CCPA/HIPAA requirements
- **Audits:** Pass external compliance audits
- **Incidents:** Zero data breach incidents

## Risk Mitigation

### Technical Risks:
- **Performance degradation** → Lazy loading, caching, progressive detection
- **False positives** → Confidence thresholds, context validation, user overrides
- **False negatives** → Multi-layer detection (regex + ML), regular updates
- **Integration complexity** → Backward compatibility, feature flags, gradual rollout

### Operational Risks:
- **Presidio service availability** → Fallback to local regex, circuit breakers
- **Compliance violations** → Regular audits, legal review, industry benchmarks
- **Maintenance burden** → Automated testing, monthly pattern reviews

### Security Risks:
- **Data leakage in logs** → Structured logging with masking
- **Encryption key management** → Key rotation, secure storage (Vault/KMS)

## Cost-Benefit Analysis

### Development Costs:
- **Phase 1:** 15 days (1.5 engineer-months)
- **Phase 2:** 10 days (1.0 engineer-month)
- **Phase 3:** 5 days (0.5 engineer-month)
- **Total:** 30 days (3 engineer-months)

### Ongoing Costs:
- **Maintenance:** 2-4 hours/week
- **Presidio Infrastructure:** $100-500/month
- **Monitoring:** $50-200/month

### Benefits:
- Avoid $20M+ GDPR/HIPAA fines
- Enable enterprise deployments requiring DLP
- Increase user trust in privacy
- Automated privacy checks vs manual review

### ROI Timeline:
- **Immediate:** Compliance requirements met
- **3 months:** Reduced manual review costs
- **6 months:** Positive ROI for enterprise deployments

## Conclusion

This plan provides a pragmatic, production-ready approach to implementing advanced privacy filtering for LiteLLM:

✅ **Leverages existing infrastructure (Presidio)** - faster time-to-market

✅ **Python-first** - aligns with codebase and ecosystem

✅ **Hybrid detection (regex + ML)** - balances performance and accuracy

✅ **Compliance-focused** - GDPR/CCPA/HIPAA support built-in

✅ **MCP integration** - enables future agent workflows

✅ **Clear roadmap** - 6-week timeline to production

✅ **Defer Rust** - until proven performance need

**Recommendation:** Start with Phase 1 (Enhanced Presidio) for immediate value, evaluate Phase 2 (MCP Tools) based on user needs, and defer Rust (Phase 4) unless benchmarks show necessity.

## Sources

Research based on:
- MCP Privacy Gap and Data Threats
- Securing Model Context Protocol
- MCP Specification
- LLM Guardrails Best Practices - Datadog
- Guardrails AI PII Detection
- Data Redaction Techniques 2025 - Strac
- CCPA Requirements 2026
