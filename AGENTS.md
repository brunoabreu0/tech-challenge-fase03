# Tech Challenge Fase 3 — Agent Instructions

## Role
You are a senior ML Engineer / MLOps specialist helping implement the FIAP Pós-Tech Fase 3 Tech Challenge: a medical triage NLP system with full CI/CD, monitoring, and model optimization.

## Project Summary
- **Goal**: Classify medical report text (laudos médicos) into urgency levels: normal / atenção / urgente
- **Stack**: FastAPI + sklearn (TF-IDF + LR) + ONNX Runtime + Airflow + Prometheus + Grafana + Docker
- **Repository**: `https://github.com/brunoabreu0/tech-challenge-fase03`

## Critical Rules

### Code Quality
1. Always use **Python 3.12** syntax and type hints
2. Use **Pydantic v2** for settings and schemas (`model_config = ConfigDict(...)`)
3. Apply **Ruff** formatting (line-length=88, double quotes)
4. Write **docstrings** for all public classes and functions
5. Follow `src/triage/` package layout — never put logic in the root

### Architecture Patterns (from phases 1 & 2 that got perfect scores)
1. **BaseClassifier** abstract class with `.fit()`, `.predict()`, `.save()`, `.load()`
2. **ClassifierFactory** pattern: `factory.create("tfidf_lr")` or `factory.create("onnx")`
3. **Settings** via pydantic-settings + `.env` file (never hardcode paths/config)
4. Separate concerns: `api/`, `model/`, `data/`, `settings.py`

### Docker
1. Multi-stage Dockerfile: `FROM python:3.12-slim AS builder` → `AS runtime`
2. Never COPY `.venv` or `__pycache__` into images
3. Use `ENV PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`

### Git Commits
1. Use **semantic commits**: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `refactor:`, `test:`
2. Each commit = one logical deliverable
3. Never commit: `.env`, `models/*.joblib`, `models/*.onnx`, `data/raw/`, `data/processed/`

### Monitoring
1. Use `prometheus_client` in FastAPI — Counter and Histogram
2. Expose `/metrics` endpoint in FastAPI
3. Grafana must have **minimum 3 panels**: request count, latency, error rate
4. Grafana dashboards must be **provisioned via JSON** (not manual UI setup)

### Airflow DAG
1. DAG ID: `medical_triage_training`
2. Tasks: `ingest` → `preprocess` → `train` → `save_model`
3. Use `PythonOperator` for all tasks
4. Schedule: `@weekly` or `None` (triggered manually in demo)

### ONNX Optimization
1. Use `skl2onnx` to convert sklearn pipeline
2. Compare latency: sklearn `.predict()` vs ONNX `session.run()`
3. Report results in README table (average ms per request)

## File References
- Context: See GEMINI.md in this repo and `/Users/brunoabreu/workspaces/postech/GEMINI.md`
- Phase 1 reference: `/Users/brunoabreu/workspaces/postech/repos/tech-challenge-fase01/`
- Phase 2 reference: `/Users/brunoabreu/workspaces/postech/repos/tech-challenge-fase02/`
- Requirements PDF: `/Users/brunoabreu/workspaces/postech/fase-3/resources/Tech Challenge Fase 3.pdf`
