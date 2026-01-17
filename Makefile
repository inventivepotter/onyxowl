.PHONY: help build run stop clean logs test shell health push pull

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
	@echo "  make run         - Run container (detached)"
	@echo "  make start       - Start with docker-compose"
	@echo "  make stop        - Stop container"
	@echo "  make restart     - Restart container"
	@echo "  make logs        - View container logs"
	@echo "  make shell       - Open shell in container"
	@echo ""
	@echo "Production:"
	@echo "  make prod        - Run in production mode (with NATS)"
	@echo "  make prod-build  - Build production image"
	@echo "  make prod-stop   - Stop production containers"
	@echo ""
	@echo "Utilities:"
	@echo "  make health      - Check API health"
	@echo "  make test        - Run tests in container"
	@echo "  make clean       - Remove container and images"
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
	@echo "Starting with docker-compose..."
	docker-compose up -d
	@echo "Container started at http://localhost:1001"
	@echo "API docs: http://localhost:1001/docs"

stop:
	@echo "Stopping container..."
	docker-compose down || docker stop $(CONTAINER_NAME) && docker rm $(CONTAINER_NAME)

restart: stop start

logs:
	@echo "Viewing logs..."
	docker-compose logs -f || docker logs -f $(CONTAINER_NAME)

shell:
	@echo "Opening shell in container..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Production commands
prod:
	@echo "Starting in production mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production containers started"

prod-build:
	@echo "Building production image..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-stop:
	@echo "Stopping production containers..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Utility commands
health:
	@echo "Checking API health..."
	@curl -s http://localhost:$(PORT)/health | python -m json.tool || echo "API not responding"

test:
	@echo "Running tests in container..."
	docker exec $(CONTAINER_NAME) pytest test_privacy_filter.py -v

clean:
	@echo "Cleaning up containers and images..."
	docker-compose down -v || true
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	@echo "Cleanup complete"

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
