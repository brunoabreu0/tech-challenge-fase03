# Regras do Projeto — Tech Challenge FIAP Pós-Tech 9MLET

## Identidade do Projeto

- **Curso:** FIAP Pós-Tech — Machine Learning Engineering
- **Turma:** 9MLET
- **Fase Atual:** 3 (de 5)
- **Histórico de Notas:** Fases 1 e 2 com nota máxima

## Convenções de Código

### Python
- Versão: **Python 3.12** (constraint `>=3.12,<3.13`)
- Gestor de dependências: **Poetry** (`pyproject.toml` + `poetry.lock`)
- Formatter e Linter: **Ruff** (`line-length = 88`, `target-version = "py312"`)
- Framework de testes: **Pytest** com **pytest-cov**
- Controle de pre-commit: `.pre-commit-config.yaml` com ruff-check, ruff-format, check-yaml, check-toml, end-of-file-fixer, trailing-whitespace

### Estrutura de Pacote
- Sempre usar **src layout**: `src/<nome_pacote>/`
- Declarar o pacote no `pyproject.toml` em `[tool.poetry].packages`
- Adicionar `pythonpath = ["src"]` no `[tool.pytest.ini_options]`

### Tipagem e APIs
- Type hints em **todas** as funções e métodos públicos
- **Pydantic v2** para schemas de entrada/saída da API e Settings (`model_config = ConfigDict(...)`)
- **pydantic-settings** para configuração a partir de `.env`

## Padrões Arquiteturais Obrigatórios

1. **Classes Abstratas** para contratos de modelos ML (ex.: `BaseClassifier`)
2. **Padrão Factory** para instanciação de modelos por string
3. **Settings centralizadas** via `pydantic-settings` — nunca hardcodar paths
4. **Docker multi-stage** (builder + runtime) baseado em `python:3.12-slim`
5. **`.env.example`** sempre documentado com todos os campos

## Regras de Commits

### Formato
```
<tipo>: <descrição curta em minúsculas>
```

### Tipos válidos
- `feat:` — nova funcionalidade
- `fix:` — correção de bug
- `docs:` — documentação apenas
- `ci:` — mudanças em CI/CD workflows
- `chore:` — tarefas de manutenção (deps, tooling)
- `refactor:` — refatoração sem mudança de comportamento
- `test:` — adição ou modificação de testes

### Regras
1. **Um commit por entregável** — commits granulares e orgânicos
2. **Nunca commitar:** `.env`, modelos treinados (`*.joblib`, `*.onnx`, `*.pkl`), dados brutos (`data/raw/`), dados processados (`data/processed/`), `.venv/`, `__pycache__/`
3. Commits na `main` via **Pull Request** (proteção de branch)
4. Estratégia de merge: **Squash and Merge** (mantém histórico limpo)

## Documentação

### README.md (obrigatório)
Estrutura numerada com:
1. Links oficiais (repo, vídeo, API produção)
2. Quick Start para banca avaliadora
3. Pré-requisitos com tabela de versões
4. Visão geral do projeto
5. Estrutura de diretórios
6. Tecnologias utilizadas
7. Instalação local
8. Variáveis de ambiente
9. Execução de testes
10. Docker / Docker Compose
11. CI/CD
12. Infraestrutura Cloud (Terraform)
13. Vídeo STAR

### Entrega
- Arquivo `entrega-tech-challenge-grupoXX.md` com links oficiais
- Vídeo YouTube (≤5 min) usando método STAR:
  - **Situation:** Contexto do problema de negócio
  - **Task:** Requisitos técnicos
  - **Action:** Arquitetura e decisões implementadas
  - **Result:** Demonstração funcionando com métricas

## Infraestrutura Cloud (AWS)

### Padrão Terraform
- `terraform/main.tf` — provider, backend S3 para state
- `terraform/ec2.tf` — instância EC2 (t3.micro para demos)
- `terraform/variables.tf` — variáveis configuráveis
- `terraform/outputs.tf` — outputs públicos

### Segurança Obrigatória
- **CloudFront + WAF** com geo-blocking (whitelist Brasil + Portugal)
- **Rate Limiting** WAF: 2000 req / 5min por IP
- **HTTPS** via ACM SSL
- Domínio: padrão `*.cloud-ip.cc`
- Deploy via **AWS SSM** (sem SSH direto)

## CI/CD (GitHub Actions)

### Workflow Principal (`ci.yml`)
Fases obrigatórias (em ordem):
1. Lint (Ruff)
2. Testes (Pytest)
3. Build Docker (apenas em push para `main`)

### Segredos GitHub (padrão do grupo)
- `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`

## Avaliação

Nas fases 1 e 2, a banca avalia:
1. Funcionalidade técnica (funciona mesmo sem conhecimento prévio)
2. Qualidade do código (clean code, padrões, testes)
3. Documentação clara e completa
4. Demonstração em vídeo (método STAR)
5. Histórico de commits organizado e semântico

**Sempre garantir que a banca consiga executar o projeto com os mínimo de comandos possível** (Quick Start ≤5 passos).
