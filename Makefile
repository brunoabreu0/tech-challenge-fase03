VENV = .venv
VENV_BIN = $(VENV)/bin
PYTHON = $(VENV_BIN)/python
PIP = $(VENV_BIN)/pip
PYTEST = $(VENV_BIN)/pytest
RUFF = $(VENV_BIN)/ruff
UVICORN = $(VENV_BIN)/uvicorn

.PHONY: venv install setup clean lint format test run-api train export-onnx benchmark \
        docker-build docker-run compose-up compose-down \
        tf-init tf-plan tf-apply tf-destroy

# --------------------------------------------------------------------------- #
# Ambiente local                                                               #
# --------------------------------------------------------------------------- #
$(VENV)/bin/activate:
	python3 -m venv $(VENV)

venv: $(VENV)/bin/activate

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install poetry
	$(VENV_BIN)/poetry install --with dev

setup: install
	$(VENV_BIN)/pre-commit install
	cp -n .env.example .env || true

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

# --------------------------------------------------------------------------- #
# Qualidade de código                                                          #
# --------------------------------------------------------------------------- #
lint:
	$(RUFF) check .

format:
	$(RUFF) format .

# --------------------------------------------------------------------------- #
# Testes                                                                       #
# --------------------------------------------------------------------------- #
test:
	$(PYTEST) tests/ -v

test-cov:
	$(PYTEST) tests/ -v --cov=src --cov-report=html --cov-report=term-missing

# --------------------------------------------------------------------------- #
# Modelo                                                                       #
# --------------------------------------------------------------------------- #
train:
	PYTHONPATH=src $(PYTHON) scripts/train.py

export-onnx:
	PYTHONPATH=src $(PYTHON) scripts/export_onnx.py

benchmark:
	PYTHONPATH=src $(PYTHON) scripts/benchmark_latency.py

# --------------------------------------------------------------------------- #
# API                                                                          #
# --------------------------------------------------------------------------- #
run-api:
	PYTHONPATH=src $(UVICORN) triage.api.main:app --reload --host 0.0.0.0 --port 8000

# --------------------------------------------------------------------------- #
# Docker                                                                       #
# --------------------------------------------------------------------------- #
docker-build:
	docker build -t medical-triage-api:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env medical-triage-api:latest

# --------------------------------------------------------------------------- #
# Docker Compose (API + Prometheus + Grafana)                                  #
# --------------------------------------------------------------------------- #
compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f api

# --------------------------------------------------------------------------- #
# Terraform (AWS)                                                              #
# --------------------------------------------------------------------------- #
tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply -auto-approve

tf-destroy:
	cd terraform && terraform destroy -auto-approve
