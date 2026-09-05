#!/usr/bin/env bash
# ==============================================================================
# deploy-ec2.sh — Deploy da aplicação na EC2 via AWS SSM
# Uso: bash scripts/deploy-ec2.sh
# Requer: aws cli configurado com permissões SSM
# ==============================================================================
set -euo pipefail

INSTANCE_ID="i-0bdbb4261a0c1186a"
REGION="sa-east-1"
DOCKERHUB_IMAGE="techchallengefase02/medical-triage-api:latest"
REPO_URL="https://raw.githubusercontent.com/brunoabreu0/tech-challenge-fase03/main"

echo "🚀 Iniciando deploy na EC2 ${INSTANCE_ID}..."

aws ssm send-command \
  --region "${REGION}" \
  --instance-ids "${INSTANCE_ID}" \
  --document-name "AWS-RunShellScript" \
  --comment "Deploy Medical Triage Fase 3" \
  --parameters 'commands=[
    "set -euxo pipefail",

    "# 1. Garantir que Docker e Compose estão prontos",
    "systemctl start docker || true",
    "sleep 2",

    "# 2. Criar estrutura de diretórios",
    "mkdir -p /opt/triage/monitoring/grafana/provisioning/datasources",
    "mkdir -p /opt/triage/monitoring/grafana/provisioning/dashboards",
    "mkdir -p /opt/triage/monitoring/grafana/dashboards",

    "# 3. Baixar arquivos de configuração do repositório",
    "curl -fsSL '"${REPO_URL}"'/monitoring/prometheus.yml -o /opt/triage/monitoring/prometheus.yml",
    "curl -fsSL '"${REPO_URL}"'/monitoring/grafana/provisioning/datasources/datasource.yml -o /opt/triage/monitoring/grafana/provisioning/datasources/datasource.yml",
    "curl -fsSL '"${REPO_URL}"'/monitoring/grafana/provisioning/dashboards/dashboard.yml -o /opt/triage/monitoring/grafana/provisioning/dashboards/dashboard.yml",
    "curl -fsSL '"${REPO_URL}"'/monitoring/grafana/dashboards/triage_dashboard.json -o /opt/triage/monitoring/grafana/dashboards/triage_dashboard.json",
    "curl -fsSL '"${REPO_URL}"'/docker-compose.prod.yml -o /opt/triage/docker-compose.yml",

    "# 4. Pull da imagem mais recente",
    "docker pull '"${DOCKERHUB_IMAGE}"'",

    "# 5. Parar containers antigos (se existirem)",
    "cd /opt/triage && docker compose down --remove-orphans || true",

    "# 6. Subir a stack completa",
    "cd /opt/triage && docker compose up -d",

    "# 7. Verificar status",
    "sleep 10",
    "docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\"",
    "echo Deploy concluido!"
  ]' \
  --output json \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
cmd_id = d['Command']['CommandId']
print(f'✅ Comando SSM enviado: {cmd_id}')
print(f'   Acompanhe em: https://sa-east-1.console.aws.amazon.com/systems-manager/run-command/{cmd_id}')
print(f'   Ou execute: aws ssm get-command-invocation --command-id {cmd_id} --instance-id ${INSTANCE_ID} --region ${REGION}')
"
