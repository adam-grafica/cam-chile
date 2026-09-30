.PHONY: install dev test test-cov lint seed migrate clean format bootstrap worktree ci-local help

PYTHON ?= python3.12
VENV   ?= .venv

help:
	@echo "Targets:"
	@echo "  install     - Crear venv e instalar dependencias"
	@echo "  dev         - Levantar backend en modo desarrollo"
	@echo "  test        - Correr pytest"
	@echo "  test-cov    - Pytest con coverage"
	@echo "  lint        - Ruff + black --check"
	@echo "  format      - black + isort"
	@echo "  seed        - Cargar cámaras semilla (requiere backend levantado)"
	@echo "  migrate     - Aplicar migración 001 (align_to_spec)"
	@echo "  clean       - Eliminar cache y DB local"
	@echo "  bootstrap   - scripts/bootstrap.sh"
	@echo "  worktree AGENT ISSUE SLUG - scripts/add-worktree.sh"
	@echo "  ci-local    - Correr todos los gates localmente (Issue #14)"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pip install -r requirements-dev.txt

dev:
	. .env 2>/dev/null || true; \
	$(VENV)/bin/uvicorn backend.app:app --reload --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8000}

test:
	$(VENV)/bin/pytest -q

test-cov:
	$(VENV)/bin/pytest --cov=backend --cov-report=term-missing --cov-fail-under=80

lint:
	$(VENV)/bin/ruff check backend tests
	$(VENV)/bin/black --check backend tests

format:
	$(VENV)/bin/isort backend tests
	$(VENV)/bin/black backend tests

seed:
	$(VENV)/bin/python scripts/seed_chile.py

migrate:
	$(VENV)/bin/python backend/db/migrate.py

clean:
	rm -rf backend/db/*.db backend/db/*.sqlite .coverage htmlcov/ catalog/.cache/

bootstrap:
	bash scripts/bootstrap.sh

worktree:
	bash scripts/add-worktree.sh $(AGENT) $(ISSUE) $(SLUG)

ci-local:
	@echo "▸ ruff"
	$(VENV)/bin/ruff check backend catalog tests
	@echo "▸ black"
	$(VENV)/bin/black --check backend catalog tests
	@echo "▸ pytest + coverage"
	$(VENV)/bin/pytest tests/ -v --cov=backend --cov=catalog --cov-report=term-missing --cov-fail-under=80
	@echo "▸ catalog validate"
	$(VENV)/bin/python catalog/validate.py --all
	@echo "▸ gitleaks (requiere binario en PATH; falla si detecta secretos)"
	@gitleaks detect --no-git --source .
	@echo "✓ ci-local OK"