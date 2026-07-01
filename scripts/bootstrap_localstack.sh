#!/usr/bin/env bash
# Sobe a infra no LocalStack e mostra as variaveis para colocar no .env.
# Pre-requisito: LocalStack rodando (make ls-up). Uso: bash scripts/bootstrap_localstack.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="infra/terraform/environments/localstack"
ENDPOINT="${AWS_ENDPOINT_URL:-http://localhost:4566}"

echo ">> aguardando o LocalStack em $ENDPOINT"
for _ in $(seq 1 30); do
  if curl -sf "$ENDPOINT/_localstack/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo ">> provisionando a infra do LocalStack"
terraform -chdir="$ROOT" init -input=false >/dev/null
terraform -chdir="$ROOT" apply -auto-approve

echo
echo ">> pronto. Coloque estas linhas no seu .env (modo LocalStack):"
BRONZE=$(terraform -chdir="$ROOT" output -json bucket_names | python3 -c "import sys,json;print(json.load(sys.stdin)['bronze'])")
SILVER=$(terraform -chdir="$ROOT" output -json bucket_names | python3 -c "import sys,json;print(json.load(sys.stdin)['silver'])")
GOLD=$(terraform -chdir="$ROOT" output -json bucket_names | python3 -c "import sys,json;print(json.load(sys.stdin)['gold'])")
cat <<EOF
STORAGE_BACKEND=s3
AWS_ENDPOINT_URL=$ENDPOINT
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1
BRONZE_BUCKET=$BRONZE
SILVER_BUCKET=$SILVER
GOLD_BUCKET=$GOLD
EOF
