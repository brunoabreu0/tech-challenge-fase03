# Entrega - Tech Challenge (Fase 3)

**Curso:** FIAP Pós Tech - Machine Learning Engineering
**Turma:** 9MLET

**Autores (Grupo 17):**
* Bruno Machado Abreu (RM372965)
* Renan Prado Gonzalez (RM374089)
* Davi Coene Rosa (RM371466)
* Paulo Henrique Alves Krempel (RM374144)
* Pedro Gabriel Pereira do Nascimento (RM372994)

---

## 🔗 Links Oficiais do Projeto

1. **Repositório do Código (Github):**
   * [https://github.com/brunoabreu0/tech-challenge-fase03](https://github.com/brunoabreu0/tech-challenge-fase03)
   * *Nota:* Todo o código fonte, API FastAPI, DAG Airflow, stack de monitoramento (Prometheus + Grafana), otimização ONNX e infraestrutura Terraform encontram-se neste repositório.

2. **Apresentação do Projeto (Vídeo STAR):**
   * **Link do Vídeo (YouTube):** *(adicionar após a gravação)*
   * *Nota:* Vídeo explicativo de 5 minutos detalhando a Situação, Tarefa, Ações e Resultados do sistema de triagem médica construído.

3. **Infraestrutura AWS (Terraform):**
   * *Nota (Arquitetura):* A infraestrutura foi provisionada com Terraform (pasta `terraform/`), criando EC2 + CloudFront + AWS WAF com geo-blocking (BR+PT) e rate limiting, consistente com as fases anteriores.

4. **Stack de Monitoramento:**
   * API: `http://localhost:8000/docs` — Swagger UI interativo
   * Prometheus: `http://localhost:9090`
   * Grafana: `http://localhost:3000` (admin/admin) — Dashboard auto-provisionado com 5 painéis

5. **Airflow (Pipeline de Treino):**
   * DAG `medical_triage_training`: ingest → preprocess → train → save_model
   * Execução: `docker compose -f docker-compose.airflow.yml up -d` → `http://localhost:8080`
