# Docker Deployment Guide

Complete guide for running Privacy Filter in Docker with multi-stage builds.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Docker Architecture](#docker-architecture)
- [Build Process](#build-process)
- [Running the Container](#running-the-container)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Option 1: Using Makefile (Easiest)

```bash
# Build and run
make build
make run

# Or with docker-compose
make start

# View logs
make logs

# Check health
make health

# Stop
make stop
```

### Option 2: Using Docker Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 3: Using Docker CLI

```bash
# Build
docker build -t privacy-filter:latest .

# Run
docker run -d \
  --name privacy-filter-api \
  -p 1001:1001 \
  privacy-filter:latest

# Check logs
docker logs -f privacy-filter-api
```

## 🏗️ Docker Architecture

### Multi-Stage Build

The Dockerfile uses a **multi-stage build** pattern for optimization:

```
┌─────────────────────────────────────────┐
│  Stage 1: Builder (~2.5GB)              │
│  - Python 3.11 + build tools            │
│  - Install all dependencies             │
│  - Download GLiNER model (~400MB)       │
│  - Download spaCy model (~500MB)        │
└─────────────────────────────────────────┘
                    │
                    │ Copy only necessary files
                    ▼
┌─────────────────────────────────────────┐
│  Stage 2: Runtime (~1.2GB)              │
│  - Python 3.11 slim                     │
│  - Virtual environment (from builder)   │
│  - Cached models (from builder)         │
│  - Application code only                │
└─────────────────────────────────────────┘
```

**Benefits**:
- ✅ Smaller final image (~1.2GB vs ~2.5GB)
- ✅ No build tools in production image
- ✅ Faster deployments
- ✅ Better security (smaller attack surface)

### Image Layers

```dockerfile
# Layer 1: Base image (Python 3.11-slim)
FROM python:3.11-slim

# Layer 2: System dependencies
RUN apt-get update && apt-get install...

# Layer 3: Virtual environment
COPY --from=builder /opt/venv

# Layer 4: Model cache
COPY --from=builder /root/.cache

# Layer 5: Application code
COPY privacy_filter.py api_endpoint.py
```

## 🔨 Build Process

### Standard Build

```bash
docker build -t privacy-filter:latest .
```

### Build Arguments

```bash
# Build with specific Python version
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t privacy-filter:latest .

# Build with custom GLiNER model
docker build \
  --build-arg GLINER_MODEL=urchade/gliner_large-v2.1 \
  -t privacy-filter:latest .
```

### Build Stages

```bash
# Build only the builder stage (for debugging)
docker build --target builder -t privacy-filter:builder .

# Build runtime stage (default)
docker build --target runtime -t privacy-filter:runtime .
```

### Build with Cache

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t privacy-filter:latest .

# No cache build (fresh build)
docker build --no-cache -t privacy-filter:latest .
```

## 🏃 Running the Container

### Basic Run

```bash
docker run -d \
  --name privacy-filter-api \
  -p 1001:1001 \
  privacy-filter:latest
```

### With Environment Variables

```bash
docker run -d \
  --name privacy-filter-api \
  -p 1001:1001 \
  -e WORKERS=4 \
  -e LOG_LEVEL=debug \
  privacy-filter:latest
```

### With Volume Mounts

```bash
# Persist model cache
docker run -d \
  --name privacy-filter-api \
  -p 1001:1001 \
  -v gliner-cache:/root/.cache/huggingface \
  privacy-filter:latest
```

### With Resource Limits

```bash
docker run -d \
  --name privacy-filter-api \
  -p 1001:1001 \
  --memory="2g" \
  --cpus="2" \
  privacy-filter:latest
```

## 🏭 Production Deployment

### Docker Compose Production

```bash
# Start with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or using Make
make prod
```

### Production Features

1. **NATS JetStream Session Storage**
   - Persistent session data
   - Shared across multiple instances
   - TTL-based expiration

2. **Multiple Workers**
   - Uvicorn with 4 workers
   - Better concurrency
   - Automatic request distribution

3. **Health Checks**
   - Automatic container restart
   - Load balancer integration
   - Monitoring ready

4. **Resource Limits**
   - CPU: 2-4 cores
   - Memory: 2-4GB
   - Prevents resource exhaustion

### High Availability Setup

```yaml
# docker-compose.prod.yml
services:
  privacy-filter:
    deploy:
      replicas: 3  # Run 3 instances
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

### Nginx Reverse Proxy

```nginx
# nginx.conf
upstream privacy_filter {
    server privacy-filter-1:1001;
    server privacy-filter-2:1001;
    server privacy-filter-3:1001;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://privacy_filter;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## ⚙️ Configuration

### Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit configuration
nano .env
```

**Key Variables**:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | API host |
| `PORT` | `1001` | API port |
| `WORKERS` | `1` | Uvicorn workers |
| `LOG_LEVEL` | `info` | Logging level |
| `USE_NATS` | `false` | Enable NATS |
| `NATS_URL` | `nats://localhost:4222` | NATS server URL |
| `SESSION_TTL` | `300` | Session expiration (seconds) |

### Docker Compose Override

```yaml
# docker-compose.override.yml (auto-loaded)
version: '3.8'

services:
  privacy-filter:
    environment:
      - LOG_LEVEL=debug
      - WORKERS=2
    ports:
      - "8080:1001"  # Custom port
```

## 🔍 Monitoring & Debugging

### View Logs

```bash
# Follow logs
docker logs -f privacy-filter-api

# Last 100 lines
docker logs --tail 100 privacy-filter-api

# With timestamps
docker logs -t privacy-filter-api
```

### Container Shell

```bash
# Open bash shell
docker exec -it privacy-filter-api /bin/bash

# Run Python shell
docker exec -it privacy-filter-api python

# Check installed packages
docker exec privacy-filter-api pip list
```

### Health Check

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' privacy-filter-api

# Manual health check
curl http://localhost:1001/health
```

### Resource Usage

```bash
# Container stats
docker stats privacy-filter-api

# Detailed info
docker inspect privacy-filter-api
```

## 🐛 Troubleshooting

### Issue: Container Exits Immediately

**Check logs**:
```bash
docker logs privacy-filter-api
```

**Common causes**:
- Missing dependencies
- Port already in use
- Model download failure

**Solution**:
```bash
# Rebuild without cache
docker build --no-cache -t privacy-filter:latest .
```

### Issue: Model Download Fails

**Symptoms**: Slow startup or errors on first request

**Solution**: Pre-download model during build
```bash
# Ensure download_models.py runs
docker build -t privacy-filter:latest .
```

### Issue: Out of Memory

**Symptoms**: Container killed or OOM errors

**Solution**: Increase memory limit
```bash
docker run -d --memory="4g" privacy-filter:latest
```

### Issue: Slow Performance

**Check**:
1. Are you using GPU? (Not enabled by default)
2. Multiple workers configured?
3. Model cached?

**Solution**: Use production config
```bash
make prod
```

### Issue: Port Already in Use

**Error**: `Bind for 0.0.0.0:1001 failed: port is already allocated`

**Solution**:
```bash
# Use different port
docker run -p 8001:1001 privacy-filter:latest

# Or stop conflicting container
docker ps | grep 1001
docker stop <container-id>
```

## 📊 Performance Optimization

### 1. Use Volume for Model Cache

```yaml
volumes:
  - gliner-cache:/root/.cache/huggingface
```

**Benefits**: Model loads instantly on container restart

### 2. Use BuildKit

```bash
DOCKER_BUILDKIT=1 docker build -t privacy-filter:latest .
```

**Benefits**: Faster builds, better caching

### 3. Multi-Worker Configuration

```bash
docker run -e WORKERS=4 privacy-filter:latest
```

**Benefits**: Better concurrency (4 workers = ~4x throughput)

### 4. NATS JetStream Session Storage

```yaml
services:
  nats:
    image: nats:2-alpine
    command: -js -sd /data
    volumes:
      - nats-data:/data
```

**Benefits**: Persistent sessions, shared across instances, built-in streaming

## 🔒 Security Best Practices

### 1. Non-Root User

Already implemented in Dockerfile:
```dockerfile
USER appuser  # UID 1000
```

### 2. Read-Only Root Filesystem

```bash
docker run --read-only privacy-filter:latest
```

### 3. No Privileged Mode

```bash
# Never use --privileged
docker run --privileged privacy-filter:latest  # ❌ DON'T DO THIS
```

### 4. Secrets Management

```bash
# Use Docker secrets (Swarm)
docker secret create api_key api_key.txt

# Or environment files
docker run --env-file .env.production privacy-filter:latest
```

### 5. Network Isolation

```yaml
networks:
  privacy-filter-network:
    driver: bridge
    internal: true  # No external access
```

## 🚀 Deployment Platforms

### AWS ECS

```bash
# Build for ARM64 (Graviton)
docker buildx build --platform linux/arm64 -t privacy-filter:latest .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-url>
docker tag privacy-filter:latest <ecr-url>/privacy-filter:latest
docker push <ecr-url>/privacy-filter:latest
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/<project-id>/privacy-filter

# Deploy
gcloud run deploy privacy-filter \
  --image gcr.io/<project-id>/privacy-filter \
  --platform managed \
  --memory 2Gi
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: privacy-filter
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: privacy-filter
        image: privacy-filter:latest
        ports:
        - containerPort: 1001
        resources:
          limits:
            memory: "2Gi"
            cpu: "2"
```

## 📚 Additional Resources

- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)

## 🆘 Getting Help

```bash
# Docker commands help
make help

# Container info
docker inspect privacy-filter-api

# View all containers
docker ps -a
```

---

**Ready to deploy!** 🚀
