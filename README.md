# Privacy Filter with GLiNER + Presidio

Production-ready privacy filter with **reversible masking** using hash maps. Masks PII before sending to LLM, then de-masks the response.

[![Tests](https://img.shields.io/badge/tests-610%2B%20passing-brightgreen)]() [![Coverage](https://img.shields.io/badge/coverage-comprehensive-blue)]() [![Python](https://img.shields.io/badge/python-3.9%2B-blue)]() [![Docker](https://img.shields.io/badge/docker-ready-blue)]()

**Quick Stats**: 610+ test cases | 70+ entity types | 15+ countries | Hybrid ML + Regex detection

## 🎯 Key Features

- **Hybrid Detection**: GLiNER ML + comprehensive regex patterns (70+ entity types)
- **Reversible Masking**: Hash map-based token mapping for de-masking
- **610+ Test Cases**: Comprehensive coverage across emails, phones, credit cards, SSNs, crypto
- **Multi-Country Support**: 15+ countries for phones, 7+ for national IDs
- **FastAPI REST API**: Production-ready endpoints with session management
- **Docker Ready**: Multi-stage builds, optimized for production

## 🏗️ Architecture

```
User Input (PII)
    ↓
[GLiNER Detection] → Detect entities
    ↓
[Hash Map Creation] → Token map: {{__OWL:EMAIL_1__}} → john@example.com
    ↓
Masked Text → Send to LLM
    ↓
LLM Response (with tokens)
    ↓
[De-mask using Hash Map] → Restore original values
    ↓
Response to User (with PII)
```

## 📦 Installation

### Option 1: Docker (Recommended)

```bash
# Using Makefile (easiest)
make build
make run

# Or using docker-compose
cd docker && docker-compose up -d

# Or using Docker CLI
docker build -f docker/Dockerfile -t privacy-filter:latest .
docker run -d -p 1001:1001 privacy-filter:latest
```

**Benefits**: Pre-built image with all dependencies, ready to use! See [DOCKER.md](docs/DOCKER.md) for details.

### Option 2: Local Installation

```bash
# Install package with dependencies
pip install -e .

# Or install with dev/api extras
pip install -e ".[dev,api]"

# Download spaCy model (optional, GLiNER is primary)
python -m spacy download en_core_web_sm
```

## 🚀 Quick Start

### 1. Basic Usage (Python)

```python
from privacy_filter import PrivacyFilter

# Initialize filter
filter_instance = PrivacyFilter(use_gliner=True)

# Mask text (auto-generated session ID)
text = "Email me at john@example.com or call (555) 123-4567"
result = filter_instance.mask(text)

# Or with custom session ID
result = filter_instance.mask(text, session_id="my-custom-session-123")

print(result.masked_text)
# Output: "Email me at {{__OWL:EMAIL_ADDRESS_1__}} or call {{__OWL:PHONE_NUMBER_1__}}"

print(result.token_map)
# Output: {"{{__OWL:EMAIL_ADDRESS_1__}}": "john@example.com", "{{__OWL:PHONE_NUMBER_1__}}": "(555) 123-4567"}

# De-mask text
llm_response = "I'll send confirmation to {{__OWL:EMAIL_ADDRESS_1__}}"
demasked = filter_instance.demask(llm_response, session_id=result.session_id)

print(demasked.original_text)
# Output: "I'll send confirmation to john@example.com"
```

### 2. API Server

**Docker (Recommended):**
```bash
# Using Makefile
make start

# Or using docker-compose
cd docker && docker-compose up -d

# View logs
make logs
```

**Local:**
```bash
# Start server (option 1)
python -m api.main

# Or with uvicorn directly (option 2)
uvicorn api.main:app --host 0.0.0.0 --port 1001

# Server runs on http://localhost:1001
# API docs: http://localhost:1001/docs
```

#### API Endpoints

**Mask Text**
```bash
# Auto-generated session ID
curl -X POST "http://localhost:1001/mask" \
  -H "Content-Type: application/json" \
  -d '{"text": "My email is john@example.com"}'

# With custom session ID (useful for correlation)
curl -X POST "http://localhost:1001/mask" \
  -H "Content-Type: application/json" \
  -d '{"text": "My email is john@example.com", "session_id": "my-custom-session-123"}'
```

**De-mask Text**
```bash
curl -X POST "http://localhost:1001/demask" \
  -H "Content-Type: application/json" \
  -d '{
    "masked_text": "Send confirmation to {{__OWL:EMAIL_ADDRESS_1__}}",
    "session_id": "your-session-id"
  }'
```

**Complete LLM Flow**
```bash
# Step 1: Mask user input
curl -X POST "http://localhost:1001/llm-flow" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "My email is alice@company.com"}'

# Step 2: De-mask LLM response
curl -X POST "http://localhost:1001/llm-flow" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_response": "I will email {{__OWL:EMAIL_ADDRESS_1__}}",
    "session_id": "session-id-from-step-1"
  }'
```

### 3. Complete LLM Workflow Example

```python
import requests
from openai import OpenAI

# Initialize
BASE_URL = "http://localhost:1001"
openai_client = OpenAI()

# User input with PII
user_message = "My email is john@example.com and I need help with my account"

# Step 1: Mask user input
mask_response = requests.post(
    f"{BASE_URL}/mask",
    json={"text": user_message}
).json()

masked_input = mask_response["masked_text"]
session_id = mask_response["session_id"]

print(f"Masked: {masked_input}")
# Output: "My email is {{__OWL:EMAIL_ADDRESS_1__}} and I need help with my account"

# Step 2: Send to LLM
llm_response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": masked_input}]
).choices[0].message.content

print(f"LLM Response: {llm_response}")
# LLM might say: "I can help! I'll send confirmation to {{__OWL:EMAIL_ADDRESS_1__}}"

# Step 3: De-mask LLM response
demask_response = requests.post(
    f"{BASE_URL}/demask",
    json={
        "masked_text": llm_response,
        "session_id": session_id
    }
).json()

final_response = demask_response["original_text"]
print(f"Final Response: {final_response}")
# Output: "I can help! I'll send confirmation to john@example.com"

# Step 4: Clean up
requests.delete(f"{BASE_URL}/session/{session_id}")
```

## 🔍 Supported Entity Types

### Personal Information (270 test cases)
- `EMAIL_ADDRESS` - 120+ variations (Unicode, international domains, edge cases)
- `PHONE_NUMBER` - 150+ variations across 15+ countries (US, UK, India, Australia, Germany, France, Japan, China, Brazil, Mexico, Korea, Spain, Italy)
- `PERSON` - Names

### Financial (140 test cases)
- `CREDIT_CARD` - Visa, Mastercard, Amex, Discover, JCB, Diners Club, Maestro, UnionPay
- `IBAN_CODE` - IBAN codes

### National IDs (100 test cases)
- `US_SSN` - US Social Security Numbers
- `UK_NINO` - UK National Insurance Number
- `CANADIAN_SIN` - Canadian Social Insurance Number
- `AUSTRALIAN_TFN` - Australian Tax File Number
- `INDIAN_AADHAAR` - Indian Aadhaar Number
- `GERMAN_TAX_ID` - German Tax ID
- `FRENCH_INSEE` - French INSEE Number

### Cryptocurrency (100 test cases)
- `BITCOIN_ADDRESS` - Bitcoin (Legacy & SegWit)
- `ETHEREUM_ADDRESS` - Ethereum
- `LITECOIN_ADDRESS` - Litecoin
- `DOGECOIN_ADDRESS` - Dogecoin
- `RIPPLE_ADDRESS` - Ripple (XRP)
- `MONERO_ADDRESS` - Monero

### Secrets & Credentials
- `AWS_ACCESS_KEY_ID` - AWS keys
- `API_KEY` - Generic API keys
- `PASSWORD` - Passwords
- `JWT_TOKEN` - JWT tokens

### Location & Network
- `LOCATION` - Physical addresses
- `IP_ADDRESS` - IP addresses

### Health
- `MEDICAL_LICENSE` - Medical licenses

**Total: 610+ comprehensive test cases** covering global formats and edge cases.

## 🎨 Advanced Features

### Custom Session ID

You can provide your own session ID for correlation or predictable identifiers:

```python
# Python
result = filter_instance.mask(
    text,
    session_id="user-123-conversation-456"
)
# result.session_id == "user-123-conversation-456"
```

```bash
# API
curl -X POST "http://localhost:1001/mask" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Email me at john@example.com",
    "session_id": "user-123-conversation-456"
  }'
```

This is useful for:
- **Correlation**: Link mask/demask operations across services
- **Idempotency**: Use predictable IDs for retry logic
- **Multi-turn conversations**: Maintain same session across messages

### Selective Entity Masking

By default, all supported entity types are masked. Use `entities_to_mask` to only mask specific types:

**Python:**
```python
# Only mask emails and phone numbers, leave other PII visible
result = filter_instance.mask(
    text,
    entities_to_mask=["EMAIL_ADDRESS", "PHONE_NUMBER"]
)

# Only mask financial data
result = filter_instance.mask(
    text,
    entities_to_mask=["CREDIT_CARD", "IBAN_CODE", "US_SSN"]
)
```

**API:**
```bash
curl -X POST "http://localhost:1001/mask" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Contact john@example.com or call 555-1234. SSN: 123-45-6789",
    "entities_to_mask": ["EMAIL_ADDRESS", "PHONE_NUMBER"]
  }'
# Result: SSN remains visible, only email and phone are masked
```

**Available Entity Types:**

| Category | Entity Types |
|----------|-------------|
| Personal | `EMAIL_ADDRESS`, `PHONE_NUMBER`, `PERSON` |
| Financial | `CREDIT_CARD`, `IBAN_CODE` |
| National IDs | `US_SSN`, `UK_NINO`, `CANADIAN_SIN`, `AUSTRALIAN_TFN`, `INDIAN_AADHAAR`, `GERMAN_TAX_ID`, `FRENCH_INSEE` |
| Crypto | `BITCOIN_ADDRESS`, `ETHEREUM_ADDRESS`, `LITECOIN_ADDRESS`, `DOGECOIN_ADDRESS`, `RIPPLE_ADDRESS`, `MONERO_ADDRESS` |
| Secrets | `AWS_ACCESS_KEY_ID`, `API_KEY`, `PASSWORD`, `JWT_TOKEN` |
| Other | `LOCATION`, `IP_ADDRESS`, `MEDICAL_LICENSE` |

**Use Cases:**
- Mask only financial data when processing payment-related queries
- Keep names visible for personalization while masking contact info
- Selectively mask based on compliance requirements (GDPR, HIPAA, PCI-DSS)

### Custom Token Format

The default token format is `{{__OWL:ENTITY_TYPE_INDEX__}}`:
- `{{__OWL:EMAIL_ADDRESS_1__}}`
- `{{__OWL:PHONE_NUMBER_2__}}`

This format is:
- **Unique**: Each entity gets a numbered token
- **LLM-Safe**: Double curly braces + `OWL` prefix prevents LLM misinterpretation
- **Parseable**: Easy regex pattern: `\{\{__OWL:[A-Z_]+_\d+__\}\}`
- **Branded**: `OWL` prefix clearly identifies OnyxOwl tokens

### Using Tokens with LLMs

When integrating with LLMs, add this instruction to your system prompt to ensure tokens are preserved:

```
Strings matching {{__OWL:[A-Z_]+_\d+__}} are internal reference tokens.
Preserve them exactly as-is. Do not attempt to resolve, substitute, or interpret their values.
```

**Why this pattern?**

| Pattern | Problem |
|---------|---------|
| `[EMAIL_1]` | Looks like markdown links, citations |
| `<EMAIL_1>` | Looks like XML/HTML tags |
| `{EMAIL_1}` | Common in templating, may be interpreted |
| `{{__OWL:EMAIL_1__}}` | Unique, branded, unambiguous |

**Tool Integration Example:**

When LLMs call tools with masked arguments, use the `/resolve` endpoint to get real values:

```python
# LLM wants to call: send_email(to={{__OWL:EMAIL_ADDRESS_1__}})
# Before executing, resolve the token:

response = requests.post(
    f"{BASE_URL}/resolve",
    json={
        "session_id": session_id,
        "tokens": ["{{__OWL:EMAIL_ADDRESS_1__}}"]
    }
)
resolved = response.json()["resolved"]
# resolved = {"{{__OWL:EMAIL_ADDRESS_1__}}": "john@example.com"}

# Now call the tool with real value
send_email(to=resolved["{{__OWL:EMAIL_ADDRESS_1__}}"])
```

## 🔒 Security Considerations

1. **Session Storage**: Token maps are stored in memory
   - For production: Use NATS JetStream with encryption (see [NATS_SESSION_MANAGEMENT.md](docs/NATS_SESSION_MANAGEMENT.md))
   - Always clean up sessions after use

2. **Token Maps**: Never log or expose token maps
   - Contains original PII values
   - Treat as sensitive data

3. **HTTPS**: Always use HTTPS in production
   - Token maps transmitted over network

4. **Expiration**: Implement session expiration
   - Default: No expiration (manual cleanup required)
   - Recommended: 5-15 minute TTL

## 📊 Performance

- **GLiNER Detection**: ~50-100ms per request
- **Masking**: ~1-2ms
- **De-masking**: <1ms
- **Total Latency**: ~50-100ms per request

## 🧪 Testing

### Run Examples
```bash
# Run example usage
python examples/usage.py
```

### Run Test Suite (610+ tests)

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src/privacy_filter --cov-report=html

# Run tests in parallel (faster)
pytest tests/ -n auto
```

### Run Tests by Category

```bash
# Email tests (120 cases)
pytest tests/test_emails.py -v

# Phone tests (150 cases)
pytest tests/test_phones.py -v

# Credit card tests (140 cases)
pytest tests/test_credit_cards.py -v

# SSN/National ID tests (100 cases)
pytest tests/test_ssn.py -v

# Cryptocurrency tests (100 cases)
pytest tests/test_crypto.py -v
```

### Test Coverage

| Category | Test Cases | Coverage |
|----------|-----------|----------|
| Emails | 120 | Unicode, international, edge cases |
| Phone Numbers | 150 | 15+ countries |
| Credit Cards | 140 | All major card types |
| SSN/National IDs | 100 | 7 countries |
| Cryptocurrency | 100 | 5+ currencies |
| **Total** | **610+** | **Comprehensive global coverage** |

## 🚧 Production Deployment

### Docker Production (Recommended)

```bash
# Start with NATS and multiple workers
make prod

# Or using docker-compose
cd docker && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
cd docker && docker-compose ps

# View logs
cd docker && docker-compose logs -f
```

**Production features included**:
- ✅ NATS JetStream session storage with TTL
- ✅ Multiple Uvicorn workers (4x throughput)
- ✅ Health checks and auto-restart
- ✅ Resource limits (CPU/memory)
- ✅ Volume persistence for model cache

See [DOCKER.md](docs/DOCKER.md) for complete deployment guide.

### Manual Production Setup

#### 1. Add Session Persistence (NATS JetStream)

See [NATS_SESSION_MANAGEMENT.md](docs/NATS_SESSION_MANAGEMENT.md) for complete NATS integration guide.

```python
from nats_session_store import NATSSessionStore

class PrivacyFilter:
    def __init__(self):
        self.session_store = NATSSessionStore(
            nats_url="nats://localhost:4222",
            ttl_seconds=300  # 5 minute TTL
        )

    async def mask(self, text):
        # ... existing code ...
        # Store in NATS JetStream with expiration
        await self.session_store.store_session(
            session_id,
            token_map
        )
```

#### 2. Add Authentication

```python
from fastapi import Depends, HTTPException, Header

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.post("/mask", dependencies=[Depends(verify_api_key)])
async def mask_text(request: MaskRequest):
    # ... existing code ...
```

#### 3. Add Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/mask")
@limiter.limit("10/minute")
async def mask_text(request: MaskRequest):
    # ... existing code ...
```

## 📝 Roadmap

- [x] Comprehensive tests (610+ test cases)
- [x] Multi-country support (15+ countries)
- [x] Docker deployment with production config
- [x] Hybrid detection (GLiNER + regex)
- [x] Session expiration (TTL) with NATS JetStream
- [ ] Authentication/authorization
- [ ] Rate limiting
- [ ] Monitoring/logging (Prometheus/Grafana)
- [ ] Confidence thresholds configuration
- [ ] Batch processing API
- [ ] Canary token injection (leak detection)
- [ ] Hallucination detection integration

## 🤔 Why GLiNER over spaCy?

| Feature | GLiNER | spaCy |
|---------|--------|-------|
| Zero-shot learning | ✅ Yes | ❌ No |
| Custom entities | ✅ Easy | ⚠️ Requires training |
| Accuracy (PII) | 94%+ | 87%+ |
| Speed | Fast | Faster |
| Model size | 400MB | 500MB+ |
| Fine-tuning | Optional | Required |

**Recommendation**: Use GLiNER for flexibility and accuracy, especially for privacy use cases.

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build and run (development)
make build && make run

# Production with NATS
make prod

# View all commands
make help
```

### Docker Files Structure

```
docker/
├── Dockerfile                 # Multi-stage builder pattern
├── docker-compose.yml         # Development configuration
├── docker-compose.prod.yml    # Production with NATS
└── .dockerignore              # Optimize build context

Makefile                       # Convenient commands (root)
DOCKER.md                      # Complete Docker guide
```

### Image Specifications

- **Base**: Python 3.11-slim
- **Build Pattern**: Multi-stage (builder + runtime)
- **Final Size**: ~1.2GB (optimized)
- **Model Cache**: Pre-downloaded GLiNER model
- **Security**: Non-root user, minimal dependencies

See [DOCKER.md](DOCKER.md) for complete deployment guide including:
- Multi-stage build details
- Production deployment with NATS
- Kubernetes/Cloud deployment
- Performance optimization
- Security best practices

## 📁 Project Structure

```
onyxowl/
├── src/privacy_filter/        # Main package
│   ├── __init__.py           # Package exports
│   ├── core.py               # PrivacyFilter class
│   ├── gliner_engine.py      # GLiNER + regex detection
│   ├── models.py             # Data models & enums
│   └── patterns.py           # Comprehensive regex patterns
│
├── tests/                     # Test suite (610+ cases)
│   ├── conftest.py           # Pytest configuration
│   ├── test_emails.py        # 120 email tests
│   ├── test_phones.py        # 150 phone tests
│   ├── test_credit_cards.py  # 140 credit card tests
│   ├── test_ssn.py           # 100 SSN/ID tests
│   ├── test_crypto.py        # 100 crypto tests
│   └── fixtures/test_data.py # Test data
│
├── api/                       # FastAPI application
│   ├── __init__.py
│   └── main.py               # API endpoints
│
├── examples/                  # Usage examples
│   └── usage.py
│
├── docker/                    # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── .dockerignore
│
├── setup.py                   # Package setup
├── pyproject.toml            # Modern Python config
├── requirements.txt          # Dependencies
├── Makefile                  # Convenience commands
└── README.md                 # This file
```

See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed documentation.

## 📚 References

- [GLiNER Paper](https://arxiv.org/abs/2311.08526)
- [Presidio Documentation](https://microsoft.github.io/presidio/)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Docker Deployment Guide](docs/DOCKER.md)
- [LLM Security Ideas](LLM_SECURITY_IDEAS.md)

## 📄 License

MIT License
