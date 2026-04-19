.PHONY: install dev test test-unit test-e2e lint format run clean

PYTHON := python
VENV := .venv/bin/python
PIP := .venv/bin/pip

install:
	uv venv .venv
	uv pip install -r requirements.txt

dev: install
	$(PIP) install pytest pytest-cov flake8 isort black pre-commit
	pre-commit install

test:
	$(VENV) -m pytest tests/ -v

test-unit:
	$(VENV) -m pytest tests/ -v -m "not e2e"

test-e2e:
	$(VENV) -m pytest tests/test_e2e.py -v -m e2e

test-cov:
	$(VENV) -m pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	$(VENV) -m flake8 src/ tests/ --max-line-length=120 --extend-ignore=E501 --exclude=web.py
	$(VENV) -m isort --check-only --diff src/ tests/

format:
	$(VENV) -m isort src/ tests/
	$(VENV) -m black src/ tests/ --line-length=120 --exclude=web.py

run:
	$(VENV) src/web.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	rm -rf htmlcov/
