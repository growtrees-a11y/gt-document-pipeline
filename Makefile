# ── PROJ-02 Document Pipeline ─────────────────────────────────────

SHELL := /bin/bash
.PHONY: build run test worker celery-worker prod clean docker-build docker-push

# ── Local Development ────────────────────────────────────────────

test:
	python -m pytest test_main.py -v --tb=short

lint:
	ruff check .

format:
	ruff format .

setup:
	pip install -r requirements.txt

# ── Docker ───────────────────────────────────────────────────────

build:
	docker compose build

run:
	docker compose up --remove-orphans

down:
	docker compose down

logs:
	docker compose logs -f

worker:
	docker compose up worker

celery-worker:
	docker compose run --rm worker

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --remove-orphans

docker-build:
	docker build -t document-pipeline:latest -f Dockerfile .
	docker build -t document-pipeline-worker:latest -f Dockerfile.worker .

docker-push:
	docker push document-pipeline:latest
	docker push document-pipeline-worker:latest

clean:
	docker compose down --volumes --remove-orphans
	docker system prune -f

# ── CI ───────────────────────────────────────────────────────────

ci: test lint docker-build

help:
	@echo "PROJ-02 Document Pipeline"
	@echo ""
	@echo "Targets:"
	@echo "  test           Run pytest"
	@echo "  lint           Run ruff linter"
	@echo "  format         Run ruff formatter"
	@echo "  setup          Install Python deps"
	@echo "  build          Build Docker images"
	@echo "  run            Start full stack (compose)"
	@echo "  prod           Start with production overrides"
	@echo "  worker         Start Celery workers"
	@echo "  down           Stop containers"
	@echo "  logs           Tail logs"
	@echo "  clean          Remove containers + volumes"
	@echo "  ci             Run test + lint + build"
	@echo "  help           Show this help"
