.PHONY: run test lint format migrate docker-up docker-down

run:
	uvicorn app.main:app --reload

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

migrate:
	alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down
