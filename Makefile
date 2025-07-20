run:
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

run-otel:
	poetry run opentelemetry-instrument uvicorn src.main:app --host 0.0.0.0 --port 8000

db-generate:
	poetry run alembic revision --autogenerate -m "$(name)"

db-migrate:
	poetry run alembic upgrade head
