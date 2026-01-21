# Privacy Filter with GLiNER + Presidio

Production-ready privacy filter with **reversible masking** using hash maps. Masks PII before sending to LLM, then de-masks the response.

**Why not guardrails?** Traditional guardrails either permanently redact PII (losing information) or block requests entirely. This preserves user experience by masking input and de-masking the response — no data loss, no blocked requests.

## AI Pipeline Use Cases

**RAG Pre-Ingestion** — Mask PII before documents hit your vector database. Sensitive data never gets indexed while document semantics stay intact for retrieval.

**AI Gateway** — Deploy at the proxy level (LiteLLM, Kong, Envoy) to protect all LLM traffic org-wide. Mask on ingress, de-mask on egress.

**Agentic Tool Calls** — When agents call external tools, resolve masked tokens before execution.

**Multi-Agent Systems** — Mask PII as data flows between agents across trust boundaries.

**Fine-Tuning Data Prep** — Clean training datasets of PII before fine-tuning. Compliance without losing training signal.

**Logging & Observability** — Log full conversations for debugging while masking PII.

---

## Installation

**Docker (recommended):**
```bash
make build && make run
# or: cd docker && docker-compose up -d
```

**Local:**
```bash
pip install -e ".[dev,api]"
python -m spacy download en_core_web_sm  # optional
```

## Quick Start

```python
from privacy_filter import PrivacyFilter

filter = PrivacyFilter(use_gliner=True)

# Mask
text = "Email me at john@example.com or call (555) 123-4567"
result = filter.mask(text)
print(result.masked_text)
# "Email me at {{__OWL:EMAIL_ADDRESS_1__}} or call {{__OWL:PHONE_NUMBER_1__}}"

# De-mask
llm_response = "I'll send confirmation to {{__OWL:EMAIL_ADDRESS_1__}}"
demasked = filter.demask(llm_response, session_id=result.session_id)
print(demasked.original_text)
# "I'll send confirmation to john@example.com"
```

### API

Start the server:
```bash
make start  # or: uvicorn api.main:app --port 1001
```

Endpoints:
```bash
# Mask
curl -X POST "http://localhost:1001/mask" \
  -H "Content-Type: application/json" \
  -d '{"text": "My email is john@example.com"}'

# De-mask
curl -X POST "http://localhost:1001/demask" \
  -H "Content-Type: application/json" \
  -d '{"masked_text": "...", "session_id": "..."}'
```

API docs at http://localhost:1001/docs

## Supported Entities

**Personal** — `EMAIL_ADDRESS`, `PHONE_NUMBER` (15+ countries), `PERSON`

**Financial** — `CREDIT_CARD` (Visa, Mastercard, Amex, etc.), `IBAN_CODE`

**National IDs** — `US_SSN`, `UK_NINO`, `CANADIAN_SIN`, `AUSTRALIAN_TFN`, `INDIAN_AADHAAR`, `GERMAN_TAX_ID`, `FRENCH_INSEE`

**Crypto** — `BITCOIN_ADDRESS`, `ETHEREUM_ADDRESS`, `LITECOIN_ADDRESS`, `DOGECOIN_ADDRESS`, `RIPPLE_ADDRESS`, `MONERO_ADDRESS`

**Secrets** — `AWS_ACCESS_KEY_ID`, `API_KEY`, `PASSWORD`, `JWT_TOKEN`

**Other** — `LOCATION`, `IP_ADDRESS`, `MEDICAL_LICENSE`

## Selective Masking

Mask only specific entity types:

```python
result = filter.mask(text, entities_to_mask=["EMAIL_ADDRESS", "PHONE_NUMBER"])
# SSN, credit cards, etc. remain visible
```

## Token Format

Tokens look like `{{__OWL:EMAIL_ADDRESS_1__}}`. The format is designed to be unambiguous to LLMs — won't be confused with markdown, XML, or template syntax.

Add this to your system prompt:
```
Strings matching {{__OWL:[A-Z_]+_\d+__}} are internal reference tokens.
Preserve them exactly as-is.
```

## Security

- **Session storage**: In-memory by default. Use NATS JetStream for production (see [NATS docs](docs/NATS_SESSION_MANAGEMENT.md))
- **Token maps contain PII** — never log them
- **Use HTTPS** in production
- **Set TTL** — recommend 5-15 minute expiration

## Performance

- GLiNER detection: ~50-100ms
- Masking: ~1-2ms
- De-masking: <1ms

## Testing

```bash
pytest tests/ -v                    # all 610+ tests
pytest tests/ -n auto               # parallel
pytest tests/ --cov=src/privacy_filter  # coverage
```

## Production

```bash
make prod  # starts with NATS + multiple workers
```

See [DOCKER.md](docs/DOCKER.md) for the full deployment guide.

## Why GLiNER over spaCy?

GLiNER does zero-shot entity recognition — no training needed for custom entity types. Better accuracy for PII (94%+ vs 87%+), and you can add new entity types without retraining.

## Roadmap

- [x] 610+ test cases
- [x] Multi-country support
- [x] Docker + NATS production config
- [x] Hybrid detection (GLiNER + regex)
- [ ] Rate limiting
- [ ] Batch processing API
- [ ] Hallucination detection

## References

- [GLiNER Paper](https://arxiv.org/abs/2311.08526)
- [Presidio Documentation](https://microsoft.github.io/presidio/)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Docker Guide](docs/DOCKER.md)

## License

MIT
