.PHONY: help build run stop clean logs test test-local test-nats shell health push pull

# Variables
IMAGE_NAME = privacy-filter
IMAGE_TAG = latest
CONTAINER_NAME = privacy-filter-api
PORT = 1001

# Default target
help:
	@echo "Privacy Filter Docker Commands"
	@echo "==============================="
	@echo ""
	@echo "Development:"
	@echo "  make build       - Build Docker image"
	@echo "  make run         - Run container only (no NATS)"
	@echo "  make start       - Start with docker-compose (includes NATS)"
	@echo "  make stop        - Stop containers"
	@echo "  make restart     - Restart containers"
	@echo "  make logs        - View container logs"
	@echo "  make shell       - Open shell in container"
	@echo ""
	@echo "Production:"
	@echo "  make prod        - Run in production mode"
	@echo "  make prod-build  - Build production image"
	@echo "  make prod-stop   - Stop production containers"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests (auto-starts NATS)"
	@echo "  make test-local  - Run KDF encryption tests only (no NATS)"
	@echo "  make test-nats   - Run NATS tests only"
	@echo ""
	@echo "Utilities:"
	@echo "  make health      - Check API health"
	@echo "  make clean       - Remove containers and images"
	@echo "  make prune       - Remove all unused Docker resources"
	@echo ""

# Development commands
build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) -f docker/Dockerfile .

run: build
	@echo "Running container..."
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):1001 \
		-v gliner-cache:/home/appuser/.cache/huggingface \
		$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "Container started at http://localhost:$(PORT)"
	@echo "API docs: http://localhost:$(PORT)/docs"

start:
	@echo "Starting with docker-compose (includes NATS)..."
	docker-compose -f docker/docker-compose.yml up -d
	@echo "Container started at http://localhost:1001"
	@echo "API docs: http://localhost:1001/docs"
	@echo "NATS monitoring: http://localhost:8222"

stop:
	@echo "Stopping containers..."
	docker-compose -f docker/docker-compose.yml down || docker stop $(CONTAINER_NAME) && docker rm $(CONTAINER_NAME)

restart: stop start

logs:
	@echo "Viewing logs..."
	docker-compose -f docker/docker-compose.yml logs -f || docker logs -f $(CONTAINER_NAME)

shell:
	@echo "Opening shell in container..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Production commands
prod:
	@echo "Starting in production mode..."
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
	@echo "Production containers started"

prod-build:
	@echo "Building production image..."
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml build

prod-stop:
	@echo "Stopping production containers..."
	docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml down

# Utility commands
health:
	@echo "Checking API health..."
	@curl -s http://localhost:$(PORT)/health | python -m json.tool || echo "API not responding"

test:
	@echo "Starting NATS for tests..."
	@docker run -d --name test-nats -p 4222:4222 nats:2.10-alpine --jetstream 2>/dev/null || true
	@sleep 2
	@echo "Running all tests..."
	@. venv/bin/activate && PYTHONPATH=src pytest tests/ -v; \
	EXIT_CODE=$$?; \
	docker stop test-nats 2>/dev/null || true; \
	docker rm test-nats 2>/dev/null || true; \
	exit $$EXIT_CODE

clean:
	@echo "Cleaning up containers and images..."
	docker-compose -f docker/docker-compose.yml down -v || true
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	@echo "Cleanup complete"

test-local:
	@echo "Running tests locally (KDF only, no NATS)..."
	. venv/bin/activate && PYTHONPATH=src pytest tests/test_nats.py::TestKDFEncryption -v

test-nats:
	@echo "Starting NATS for tests..."
	@docker run -d --name test-nats -p 4222:4222 nats:2.10-alpine --jetstream 2>/dev/null || true
	@sleep 2
	@echo "Running NATS tests..."
	@. venv/bin/activate && PYTHONPATH=src pytest tests/test_nats.py -v -m nats; \
	EXIT_CODE=$$?; \
	docker stop test-nats 2>/dev/null || true; \
	docker rm test-nats 2>/dev/null || true; \
	exit $$EXIT_CODE

prune:
	@echo "Removing all unused Docker resources..."
	docker system prune -af --volumes
	@echo "Prune complete"

# Build and push to registry (configure your registry)
push:
	@echo "Pushing to registry..."
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) your-registry/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push your-registry/$(IMAGE_NAME):$(IMAGE_TAG)

pull:
	@echo "Pulling from registry..."
	docker pull your-registry/$(IMAGE_NAME):$(IMAGE_TAG)
	docker tag your-registry/$(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_NAME):$(IMAGE_TAG)
