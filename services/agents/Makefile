.PHONY: dev test install format lint

install:
	pip install -r requirements.txt

dev: install
	LOG_LEVEL=INFO uvicorn app.main:app --reload --host 0.0.0.0 --port 5555 --log-level debug

test: install
	pytest

format:
	black .
	isort .

lint:
	flake8 .
	mypy .

.PHONY: format lint 
