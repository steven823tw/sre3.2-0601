.PHONY: help setup dev test lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup development environment
	docker compose up -d
	cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev: ## Start development servers
	docker compose up -d postgres redis
	cd backend && uvicorn app.main:app --reload --port 8688 &
	cd frontend && npm run dev

test: ## Run all tests
	cd backend && pytest tests/ -v --cov=app
	cd frontend && npm run test
	cd tests/e2e && npx playwright test

test-backend: ## Run backend tests
	cd backend && pytest tests/ -v --cov=app --cov-report=html

test-frontend: ## Run frontend tests
	cd frontend && npm run test

test-e2e: ## Run E2E tests
	cd tests/e2e && npx playwright test

lint: ## Run linters
	cd backend && ruff check app/ && mypy app/
	cd frontend && npm run lint && npx tsc --noEmit

format: ## Format code
	cd backend && ruff format app/
	cd frontend && npm run format

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name dist -exec rm -rf {} +

db-migrate: ## Run database migrations
	cd backend && alembic upgrade head

db-seed: ## Seed database with test data
	cd db/seeds && python generate_test_data.py

db-reset: ## Reset database
	docker compose down -v
	docker compose up -d postgres redis
	sleep 5
	cd backend && alembic upgrade head
	cd db/seeds && python generate_test_data.py

logs: ## Show logs
	docker compose logs -f

logs-backend: ## Show backend logs
	docker compose logs -f backend

logs-frontend: ## Show frontend logs
	docker compose logs -f frontend
