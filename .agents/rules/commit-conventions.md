# Convenções de Commits — Tech Challenge FIAP 9MLET

## Filosofia

Os commits devem ser **orgânicos** — cada commit representa a conclusão real de um entregável do projeto. A banca avaliadora analisa o histórico para ver a evolução natural do desenvolvimento.

## Estrutura por Etapa (Fase 3)

### Etapa 0 — Setup e Fundação
```
chore: initial project scaffold — pyproject.toml, .gitignore, Makefile, pre-commit
feat: add base src/triage package structure with settings and data loader
feat: implement TF-IDF + Logistic Regression text classifier with sklearn pipeline
```

### Etapa 1 — API e Docker (Deploy em Nuvem)
```
feat: add FastAPI inference API with /predict, /health and /metrics endpoints
feat: add multi-stage Dockerfile for inference API service
docs: add cloud architecture decision document to README (AWS vs Azure vs GCP analysis)
feat: add baseline latency benchmark script (sklearn inference)
```

### Etapa 2 — CI/CD e Airflow
```
ci: add GitHub Actions workflow — lint (ruff) → test (pytest) → build (docker)
feat: add Airflow DAG for training pipeline — ingest → preprocess → train → save
chore: add docker-compose for Airflow local development environment
```

### Etapa 3 — Monitoramento
```
feat: instrument FastAPI with prometheus_client — request counter and latency histogram
feat: add Prometheus + Grafana to docker-compose monitoring stack
feat: add Grafana dashboard with 3 panels — total requests, latency P95, error rate
```

### Etapa 4 — ONNX e Entrega Final
```
feat: export sklearn model to ONNX format using skl2onnx
feat: add ONNX Runtime inference wrapper and latency comparison benchmark
feat: add Terraform AWS infrastructure — EC2 + CloudFront + WAF
docs: add final README with full project documentation and entrega doc with video link
```

## Anti-Patterns a Evitar

❌ `fix: various fixes` — muito vago
❌ `update files` — não semântico
❌ `WIP` — trabalho incompleto
❌ Commits com múltiplas responsabilidades não relacionadas
❌ Commits que quebram testes

## Como Verificar Antes de Commitar

```bash
# 1. Lint
poetry run ruff check .

# 2. Format
poetry run ruff format --check .

# 3. Testes
poetry run pytest tests/ -v

# 4. Só então commitar
git add -p  # adicionar interativamente (granular)
git commit -m "feat: descrição clara do entregável"
```

## Referência de Padrões dos Projetos com Nota Máxima

### Fase 1 (Grupo 85) — Exemplos de bons commits:
- `feat: implement AWS WAF, geo-blocking, and an automated EC2 reboot workflow`
- `feat: implement IAM SSM role for EC2 and add automated deployment workflow via AWS SSM`
- `ci: add GitHub Actions workflow for automated tests and Docker Hub publish`

### Fase 2 (Grupo 17) — Exemplos de bons commits:
- `feat: DVC remote S3 — cache compartilhado entre CI e dev; pipeline mais rápida`
- `feat: mlflow.db persistido em volume EC2 com bootstrap do S3`
- `docs: reescreve README completo para banca — pré-requisitos, quick start, env vars`
