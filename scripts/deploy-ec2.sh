#!/usr/bin/env bash
# ==============================================================================
# deploy-ec2.sh — Deploy da aplicação na EC2 via AWS SSM
# Uso: bash scripts/deploy-ec2.sh
# Requer: aws cli configurado com permissões SSM
# ==============================================================================
set -euo pipefail

REGION="${AWS_DEFAULT_REGION:-sa-east-1}"
REPO_URL="https://github.com/brunoabreu0/tech-challenge-fase03.git"
DOCKERHUB_IMAGE="techchallengefase02/medical-triage-api:latest"

echo "🔍 Buscando instância EC2 com a tag Name=medical-triage-nlp-api-server..."
INSTANCE_ID="${INSTANCE_ID:-$(aws ec2 describe-instances \
  --region "${REGION}" \
  --filters "Name=tag:Name,Values=medical-triage-nlp-api-server" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text)}"

if [ -z "${INSTANCE_ID}" ] || [ "${INSTANCE_ID}" == "None" ]; then
  echo "❌ Nenhuma instância EC2 ativa encontrada."
  exit 1
fi

echo "🚀 Iniciando deploy na EC2 ${INSTANCE_ID}..."

COMMAND_ID=$(aws ssm send-command \
  --region "${REGION}" \
  --instance-ids "${INSTANCE_ID}" \
  --document-name "AWS-RunShellScript" \
  --comment "Deploy Medical Triage Fase 3" \
  --parameters 'commands=[
    "set -euxo pipefail",

    "# 1. Garantir Docker em execução",
    "systemctl start docker || true",
    "sleep 2",

    "# 2. Instalar git se necessário",
    "which git || yum install -y git",

    "# 3. Clonar/atualizar o repositório",
    "if [ -d /opt/triage/repo ]; then",
    "  cd /opt/triage/repo && git pull --ff-only origin main",
    "else",
    "  mkdir -p /opt/triage",
    "  git clone '"${REPO_URL}"' /opt/triage/repo",
    "fi",

    "# 4. Criar diretórios de dados e modelos",
    "mkdir -p /opt/triage/models /opt/triage/data/raw /opt/triage/data/processed",

    "# 5. Pull de todas as imagens",
    "docker pull '"${DOCKERHUB_IMAGE}"'",
    "docker pull apache/airflow:2.10.0-python3.12",
    "docker pull prom/prometheus:latest",
    "docker pull grafana/grafana:latest",
    "docker pull postgres:15-alpine",

    "# 6. Parar stack anterior",
    "cd /opt/triage/repo && docker compose -f docker-compose.prod.yml down --remove-orphans || true",

    "# 7. Subir stack completa (API + Prometheus + Grafana + Airflow)",
    "cd /opt/triage/repo && docker compose -f docker-compose.prod.yml up -d",

    "# 8. Aguardar inicialização",
    "echo Aguardando inicializacao dos servicos...",
    "sleep 30",

    "# 9. Status final",
    "docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\"",
    "echo Deploy concluido com sucesso!"
  ]' \
  --output json \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['Command']['CommandId'])")

echo "✅ Comando SSM enviado: ${COMMAND_ID}"
echo ""
echo "Acompanhe o progresso:"
echo "  aws ssm get-command-invocation --command-id ${COMMAND_ID} --instance-id ${INSTANCE_ID} --region ${REGION} --query Status --output text"
echo ""
echo "Para ver o output completo:"
echo "  aws ssm get-command-invocation --command-id ${COMMAND_ID} --instance-id ${INSTANCE_ID} --region ${REGION}"
echo ""
echo "Ou acesse o console AWS:"
echo "  https://${REGION}.console.aws.amazon.com/systems-manager/run-command/${COMMAND_ID}"
