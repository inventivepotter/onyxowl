# Quick Start Guide

Get Privacy Filter running in **under 5 minutes** with Docker!

## ⚡ Fastest Way (Docker + Makefile)

```bash
# 1. Build and run
make build && make run

# 2. Test the API
curl http://localhost:1001/health

# 3. Try masking
curl -X POST http://localhost:1001/mask \
  -H "Content-Type: application/json" \
  -d '{"text": "My email is john@example.com"}'

# 4. View API docs
open http://localhost:1001/docs
```

Done! 🎉

## 🐳 Using Docker Compose

```bash
# Start
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

## 💻 Local Development (No Docker)

```bash
# 1. Setup
./setup.sh

# 2. Run
python api_endpoint.py

# 3. Test
curl http://localhost:1001/health
```

## 📖 Next Steps

- [Complete README](README.md) - Full documentation
- [Docker Guide](DOCKER.md) - Production deployment
- [Architecture](ARCHITECTURE.md) - System design
- [API Examples](example_usage.py) - Code examples

## 🎯 Quick Examples

### Mask sensitive data

```bash
curl -X POST http://localhost:1001/mask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My email is alice@company.com and my card is 4532-1234-5678-9010"
  }'
```

**Response:**
```json
{
  "masked_text": "My email is <EMAIL_ADDRESS_1> and my card is <CREDIT_CARD_1>",
  "session_id": "abc-123-def-456",
  "entities_found": 2,
  "token_map": {
    "<EMAIL_ADDRESS_1>": "alice@company.com",
    "<CREDIT_CARD_1>": "4532-1234-5678-9010"
  }
}
```

### De-mask text

```bash
curl -X POST http://localhost:1001/demask \
  -H "Content-Type: application/json" \
  -d '{
    "masked_text": "I will email <EMAIL_ADDRESS_1>",
    "session_id": "abc-123-def-456"
  }'
```

**Response:**
```json
{
  "original_text": "I will email alice@company.com",
  "entities_restored": 1
}
```

## 🚀 Production Deployment

```bash
# Start with NATS and multiple workers
make prod

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

See [DOCKER.md](DOCKER.md) for details.

## 🛠️ Available Commands

```bash
make build       # Build Docker image
make run         # Run container
make start       # Start with docker-compose
make stop        # Stop container
make logs        # View logs
make shell       # Open container shell
make health      # Check API health
make prod        # Production mode
make clean       # Remove containers/images
make help        # Show all commands
```

## ❓ Troubleshooting

### Port already in use

```bash
# Use different port
docker run -p 8001:1001 privacy-filter:latest
```

### Container exits immediately

```bash
# Check logs
docker logs privacy-filter-api

# Rebuild
make clean && make build
```

### Model download fails

```bash
# Pre-download during build
docker build --no-cache -t privacy-filter:latest .
```

## 📞 Getting Help

- Check [DOCKER.md](DOCKER.md) for detailed troubleshooting
- View logs: `make logs`
- Open shell: `make shell`
- Test health: `make health`

---

**Ready to use!** 🎉 Now check out the [full documentation](README.md).
