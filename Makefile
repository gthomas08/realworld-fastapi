run:
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

migrate-autogen:
	poetry run alembic revision --autogenerate -m "$(name)"

migrate-upgrade:
	poetry run alembic upgrade head
