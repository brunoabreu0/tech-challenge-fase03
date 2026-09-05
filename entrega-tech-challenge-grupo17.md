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

1. **Repositório do Código (GitHub):**
   * [https://github.com/brunoabreu0/tech-challenge-fase03](https://github.com/brunoabreu0/tech-challenge-fase03)
   * *Nota:* Código fonte, API FastAPI, pipeline de treino Airflow, stack de observabilidade (Prometheus + Grafana), inferência otimizada ONNX Runtime e IaC Terraform.

2. **Endpoints de Produção na Nuvem (AWS CloudFront + WAF + SSL Wildcard):**
   * **API de Triagem Médica (REST):** [https://api.triage.cloud-ip.cc](https://api.triage.cloud-ip.cc)
   * **Swagger UI interativo:** [https://api.triage.cloud-ip.cc/docs](https://api.triage.cloud-ip.cc/docs)
   * **Healthcheck da API:** [https://api.triage.cloud-ip.cc/health](https://api.triage.cloud-ip.cc/health)
   * **Métricas Prometheus:** [https://api.triage.cloud-ip.cc/metrics](https://api.triage.cloud-ip.cc/metrics)
   * **Airflow Webserver (Orquestração):** [https://airflow.triage.cloud-ip.cc](https://airflow.triage.cloud-ip.cc)
   * **Prometheus Server:** [https://prometheus.triage.cloud-ip.cc](https://prometheus.triage.cloud-ip.cc)
   * **Grafana Dashboards:** [https://grafana.triage.cloud-ip.cc](https://grafana.triage.cloud-ip.cc) *(admin / admin)*

3. **Apresentação do Projeto (Vídeo STAR):**
   * **Link do Vídeo (YouTube):** *(adicionar após a gravação)*
   * *Nota:* Vídeo explicativo de até 5 minutos no formato STAR (Situation, Task, Action, Result) demonstrando o fluxo completo de triagem médica e arquitetura MLOps.

4. **Infraestrutura AWS (Terraform):**
   * Provisionamento em `terraform/` criando EC2 t3.medium, 4 distribuições CloudFront com SSL ACM e AWS WAF v2 com geo-blocking (BR/PT) e rate-limiting (2000 req/5min).

5. **Pipeline de Retreino (Apache Airflow):**
   * DAG `medical_triage_training` implementada em `airflow/dags/training_pipeline.py`.
   * Orquestra as etapas: verificação de dados -> ingestão/download -> pré-processamento -> treinamento do classificador TF-IDF + Logistic Regression -> validação de métricas -> exportação ONNX.

6. **Qualidade e Testes:**
   * 64 testes automatizados cobrindo API, pré-processamento, carregamento de dados, modelo TF-IDF, exportação e inferência ONNX Runtime.
   * Cobertura de código: **89%** (superior à meta de 70%).
