# Sistema de Triagem Médica — Tech Challenge Fase 3

[![CI](https://github.com/brunoabreu0/tech-challenge-fase03/actions/workflows/ci.yml/badge.svg)](https://github.com/brunoabreu0/tech-challenge-fase03/actions/workflows/ci.yml)

Este repositório contém a entrega do trabalho de conclusão da **Fase 3** da pós-graduação **FIAP Pós Tech em Machine Learning Engineering** (9MLET).

O objetivo é construir um sistema de triagem automática de laudos médicos com **NLP**, servido via **API REST** containerizada, com pipeline **CI/CD** (GitHub Actions), orquestração de retreino (**Apache Airflow**), monitoramento (**Prometheus + Grafana**) e otimização de latência (**ONNX Runtime**).

---

## 🔗 Links Oficiais do Projeto

* **Repositório GitHub**: [brunoabreu0/tech-challenge-fase03](https://github.com/brunoabreu0/tech-challenge-fase03)
* **Vídeo de Apresentação (STAR)**: *(link a adicionar após a gravação)*
* **API em Produção (AWS)**: *(link a adicionar após o deploy)*

---

## ⚡ Quick Start — Para a Banca Avaliadora

Forma mais rápida de executar todo o sistema localmente (API + Prometheus + Grafana):

```bash
# 1. Clonar o repositório
git clone https://github.com/brunoabreu0/tech-challenge-fase03.git
cd tech-challenge-fase03

# 2. Copiar variáveis de ambiente
cp .env.example .env

# 3. Subir a stack completa (API + Prometheus + Grafana)
docker compose up --build -d

# 4. Verificar se está tudo saudável
curl http://localhost:8000/health

# 5. Fazer uma predição
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Paciente com dor torácica severa irradiando para o braço esquerdo."}'
```

Serviços disponíveis após o `docker compose up`:
| Serviço | URL |
|---|---|
| API de Triagem (Swagger UI) | http://localhost:8000/docs |
| Métricas Prometheus | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana (admin/admin) | http://localhost:3000 |

---

## 1. Pré-requisitos

| Ferramenta | Versão Mínima | Como instalar |
|---|---|---|
| **Python** | 3.12 | [python.org](https://www.python.org/downloads/) |
| **Poetry** | 2.0+ | `pip install poetry` |
| **Docker** | 24+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | v2 | Incluído no Docker Desktop |
| **Git** | 2.x | [git-scm.com](https://git-scm.com/) |

---

## 2. Contexto e Problema de Negócio

Um hospital de referência recebe diariamente centenas de laudos médicos em texto livre. A triagem manual é lenta e sujeita a erros. O objetivo é automatizar a classificação de urgência:

| Classe | Descrição |
|---|---|
| **normal** (0) | Sem necessidade de ação imediata |
| **atencao** (1) | Requer acompanhamento ou monitoramento |
| **urgente** (2) | Requer atendimento médico imediato |

---

## 3. Arquitetura de Deploy em Nuvem (Decisão Arquitetural)

### Análise Comparativa: AWS vs Azure vs GCP

Para este cenário hospitalar, foram avaliadas três opções de plataforma de nuvem:

#### ✅ AWS (Escolhida)
**Justificativa principal:** Consistência com a infraestrutura das fases anteriores (Fase 1 e Fase 2), menor curva de operação, e experiência acumulada pela equipe.

| Componente | Serviço AWS | Papel |
|---|---|---|
| **Containerização** | ECR (Elastic Container Registry) | Registry privado da imagem Docker |
| **Compute** | EC2 (t3.micro → t3.small) | Hospeda o container da API |
| **CDN + HTTPS** | CloudFront + ACM | Entrega segura com SSL |
| **Segurança** | AWS WAF | Geo-blocking (BR+PT), Rate Limiting |
| **Deploy** | AWS SSM | Deploy sem SSH direto |
| **IaC** | Terraform | Provisionamento reprodutível |

**Modo de deploy:** **Real-time (online) inference** — a API responde a requisições individuais em tempo real, pois o cenário clínico exige latência baixa (< 100ms) para triagem imediata de pacientes.

**Por que não batch?** O volume de laudos é contínuo e imprevisível. Uma API REST em tempo real é mais adequada do que processamento em lote para triagem de urgência.

#### Azure (Descartada)
- Azure Container Apps e Azure ML são excelentes, mas a equipe não tem experiência prévia acumulada
- Custo de aprendizado não justificado para projeto acadêmico com prazo definido

#### GCP (Descartada)
- Cloud Run seria uma excelente opção para containers serverless
- Vertex AI tem ferramentas avançadas de MLOps
- Descartada pela mesma razão que Azure: consistência com infraestrutura existente

### Diagrama de Arquitetura AWS

```
Internet
    │
    ▼
CloudFront (CDN + HTTPS + WAF)
    │ Geo-blocking: Brasil + Portugal
    │ Rate Limit: 2000 req/5min por IP
    ▼
EC2 t3.small
    ├── Docker: medical-triage-api:latest (porta 8000)
    ├── Docker: prometheus (porta 9090)
    └── Docker: grafana (porta 3000)
         │
         └── Airflow (docker-compose separado, treino semanal)
```

---

## 4. Stack de Tecnologias

| Camada | Tecnologia | Versão |
|---|---|---|
| **Linguagem** | Python | 3.12 |
| **Dependências** | Poetry | 2.0+ |
| **API** | FastAPI + Uvicorn | 0.115+ |
| **ML** | scikit-learn (TF-IDF + LR) | 1.5+ |
| **Otimização** | ONNX Runtime + skl2onnx | 1.20+ |
| **Orquestração** | Apache Airflow | 2.10+ |
| **Monitoramento** | Prometheus + Grafana | latest |
| **Containers** | Docker + Docker Compose | 24+ |
| **IaC** | Terraform | 1.9+ |
| **CI/CD** | GitHub Actions | — |
| **Testes** | Pytest + pytest-cov | 8.x |
| **Linting** | Ruff | 0.8+ |

---

## 5. Estrutura do Projeto

```text
├── .github/workflows/          # CI/CD (lint → test → build)
├── airflow/
│   └── dags/
│       └── training_pipeline.py  # DAG: ingestão → treino → salvamento
├── data/
│   ├── raw/                     # Dataset bruto (gitignored)
│   └── processed/               # Dados processados (gitignored)
├── models/                      # Modelos treinados (gitignored)
│   ├── classifier.joblib        # Modelo sklearn
│   └── classifier.onnx          # Modelo ONNX otimizado
├── monitoring/
│   ├── prometheus.yml           # Scrape config Prometheus
│   └── grafana/
│       └── provisioning/        # Auto-provisioning Grafana
├── scripts/
│   ├── train.py                 # Treino standalone
│   ├── export_onnx.py           # Exportação para ONNX
│   └── benchmark_latency.py     # Comparação de latência
├── src/triage/
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   ├── metrics.py           # Prometheus instrumentação
│   │   └── schemas.py           # Pydantic schemas
│   ├── data/
│   │   ├── loader.py            # Carregamento de dados
│   │   └── preprocessor.py      # Limpeza de texto
│   ├── model/
│   │   ├── base.py              # BaseClassifier (abstrato)
│   │   ├── tfidf_lr.py          # TF-IDF + Logistic Regression
│   │   ├── onnx_classifier.py   # ONNX Runtime wrapper
│   │   └── factory.py           # ClassifierFactory
│   └── settings.py              # Pydantic Settings
├── terraform/                   # IaC AWS (EC2, CloudFront, WAF)
├── tests/                       # Suíte de testes (pytest)
├── docker-compose.yml           # API + Prometheus + Grafana
├── Dockerfile                   # Imagem multi-stage da API
└── pyproject.toml               # Dependências (Poetry)
```

---

## 6. Dataset

O projeto suporta dois modos de dados:

### 6.1. Dataset Real (recomendado)
**Medical Abstracts TC Corpus** — disponível no [Kaggle](https://www.kaggle.com/datasets/chaitanyakck/medical-text).

Após download, colocar o arquivo `train.dat` em:
```
data/raw/medical_abstracts.csv
```

### 6.2. Dados Sintéticos (fallback automático)
Se o dataset real não estiver disponível, o sistema gera automaticamente **3000 amostras sintéticas** balanceadas (1000 por classe). A API inicia normalmente sem necessidade de configuração extra.

---

## 7. Instalação Local (Poetry)

```bash
# 1. Instalar Poetry
pip install poetry

# 2. Instalar dependências
poetry install --with dev

# 3. Configurar ambiente
cp .env.example .env

# 4. Treinar o modelo
poetry run python scripts/train.py

# 5. Exportar para ONNX
poetry run python scripts/export_onnx.py

# 6. Iniciar a API
poetry run uvicorn triage.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 8. Variáveis de Ambiente

```env
APP_ENV=development          # development | production
RANDOM_SEED=42               # Seed para reprodutibilidade
DATA_RAW_DIR=data/raw        # Diretório de dados brutos
DATA_PROCESSED_DIR=data/processed
MODEL_DIR=models             # Onde salvar/carregar modelos
MODEL_NAME=tfidf_lr          # tfidf_lr | onnx
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 9. API — Endpoints

### `POST /predict`
Classifica um laudo médico.

**Request:**
```json
{"text": "Paciente com dor torácica severa irradiando para o braço esquerdo."}
```

**Response:**
```json
{
  "label": "urgente",
  "label_id": 2,
  "confidence": 0.9412,
  "latency_ms": 1.823,
  "model": "onnx"
}
```

### `GET /health`
```json
{"status": "ok", "model_loaded": true, "model_name": "onnx"}
```

### `GET /metrics`
Métricas em formato Prometheus (para scraping).

### `GET /docs`
Swagger UI interativo.

---

## 10. Execução de Testes

```bash
# Todos os testes
poetry run pytest tests/ -v

# Com cobertura
poetry run pytest tests/ --cov=src --cov-report=html

# Lint
poetry run ruff check .
poetry run ruff format --check .
```

---

## 11. Docker Compose — Stack Completa

```bash
# Subir API + Prometheus + Grafana
docker compose up --build -d

# Ver logs da API
docker compose logs -f api

# Parar tudo
docker compose down
```

### Dashboard Grafana
Acesse http://localhost:3000 (credenciais: admin/admin).

O dashboard **Medical Triage API** é provisionado automaticamente com 3 painéis:
1. **Total de Requisições** — counter por endpoint e status HTTP
2. **Latência P50/P95/P99** — histograma de tempo de resposta
3. **Taxa de Erro** — percentual de respostas 5xx

---

## 12. Apache Airflow — Pipeline de Treino

DAG `medical_triage_training` com 4 tasks em sequência:

```
ingest → preprocess → train → save_model
```

```bash
# Subir Airflow localmente
docker compose -f docker-compose.airflow.yml up -d

# Acesse: http://localhost:8080 (admin/admin)
```

---

## 13. Otimização de Latência (ONNX)

```bash
# 1. Treinar o modelo sklearn
poetry run python scripts/train.py

# 2. Exportar para ONNX
poetry run python scripts/export_onnx.py

# 3. Comparar latência
poetry run python scripts/benchmark_latency.py
```

**Resultado típico:**
| Modelo | Latência Média (ms) | Speedup |
|---|---|---|
| sklearn (TF-IDF + LR) | ~3.2 ms | 1.0x |
| ONNX Runtime | ~0.8 ms | ~4x mais rápido |

---

## 14. CI/CD (GitHub Actions)

Workflow `.github/workflows/ci.yml` executado em todo push/PR para `main`:

```
lint (Ruff) → test (Pytest) → build Docker (apenas push para main)
```

---

## 15. Infraestrutura AWS (Terraform)

```bash
cd terraform
terraform init
terraform plan
terraform apply -auto-approve
```

Recursos provisionados:
- **EC2 t3.small** — host da stack Docker
- **CloudFront** — HTTPS + CDN
- **AWS WAF** — geo-blocking (BR+PT) + rate limiting

---

## 16. Autores

**Grupo 17 — FIAP Pós-Tech 9MLET**

| Nome | RM |
|---|---|
| Bruno Machado Abreu | RM372965 |
| Renan Prado Gonzalez | RM374089 |
| Davi Coene Rosa | RM371466 |
| Paulo Henrique Alves Krempel | RM374144 |
| Pedro Gabriel Pereira do Nascimento | RM372994 |
