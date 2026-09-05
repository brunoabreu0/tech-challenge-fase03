# Tech Challenge Fase 3 — Medical Triage NLP
## Contexto do Agente

Este repositório é o projeto de conclusão da **Fase 3** da pós-graduação FIAP Pós-Tech em ML Engineering (9MLET).

### Tema
Sistema de triagem automática de laudos médicos via NLP — classifica urgência em **normal / atenção / urgente**.

### Disciplinas da Fase 3
1. Deploy em Nuvem (AWS/Azure/GCP)
2. Integração com CI/CD (GitHub Actions)
3. Pipeline de Treino e Deploy Automático (Airflow)
4. Monitoração de Performance (Prometheus + Grafana)
5. Serviços de Monitoração
6. Latência e Performance em Modelos Não Estruturados (ONNX)

### Stack Principal
- **FastAPI** — API de inferência REST
- **Scikit-learn** — TF-IDF + Logistic Regression
- **ONNX Runtime + skl2onnx** — Otimização de latência
- **Apache Airflow** — Orquestração de pipeline de treino
- **Prometheus + Grafana** — Monitoramento e observabilidade
- **Docker + Docker Compose** — Containerização
- **GitHub Actions** — CI/CD (lint → test → build)
- **Terraform** — IaC AWS

### Critérios de Avaliação (pesos)
- Modelagem e Otimização (NLP + ONNX): **20%**
- CI/CD (GitHub Actions): **15%**
- Orquestração (Airflow): **15%**
- Monitoramento (Prometheus + Grafana): **20%**
- Documentação (README): **15%**
- Vídeo STAR: **15%**

### Regras do Projeto
1. Python 3.12, Poetry, Ruff, Pytest — mesmos padrões das fases anteriores
2. Commits semânticos e orgânicos (um commit por entregável)
3. README completo com Quick Start para a banca avaliadora
4. Vídeo STAR no YouTube (≤5 minutos)
5. Stack de monitoramento funcional via Docker Compose
6. Airflow DAG: ingestão → treino → salvamento do modelo
7. Comparação de latência: modelo sklearn original vs ONNX

### Dataset
Medical Abstracts TC Corpus (Kaggle) ou equivalente com ≥2000 amostras de texto médico com classificação de urgência.

### Referências dos Projetos Anteriores
- Fase 1 (Nota Máxima): `/Users/brunoabreu/workspaces/postech/repos/tech-challenge-fase01`
  - Churn prediction API com FastAPI, PyTorch, Terraform AWS
- Fase 2 (Nota Máxima): `/Users/brunoabreu/workspaces/postech/repos/tech-challenge-fase02`
  - Sistema de recomendação com DVC, MLflow, Docker, CI/CD completo

### Arquivo de Contexto Geral
Ver `/Users/brunoabreu/workspaces/postech/GEMINI.md` para padrões e convenções globais do projeto.
