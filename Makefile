.PHONY: help install dev test lint format clean docker-up docker-down

# Variables
PYTHON = python
PIP = pip
PYTEST = pytest
BLACK = black
ISORT = isort
FLAKE8 = flake8
MYPY = mypy

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PIP) install -r requirements.txt

dev: ## Install development dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

test: ## Run tests
	$(PYTEST) --cov=app --cov-report=html --cov-report=term

test-fast: ## Run tests without coverage
	$(PYTEST) -v

lint: ## Run all linting tools
	$(BLACK) --check app/ tests/
	$(ISORT) --check-only app/ tests/
	$(FLAKE8) app/ tests/
	$(MYPY) app/

format: ## Format code with black and isort
	$(BLACK) app/ tests/
	$(ISORT) app/ tests/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create new migration
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-rollback: ## Rollback last migration
	alembic downgrade -1

run: ## Run development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
	gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000