#!/usr/bin/env bash
# Esvazia os buckets e destroi o ambiente do modo escolhido.
# Uso: bash scripts/teardown.sh [localstack|aws]
set -euo pipefail

cd "$(dirname "$0")/.."
MODE="${1:-localstack}"

case "$MODE" in
  localstack)
    ROOT="infra/terraform/environments/localstack"
    ENDPOINT_FLAG="--endpoint-url ${AWS_ENDPOINT_URL:-http://localhost:4566}"
    export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
    export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
    ;;
  aws)
    ROOT="infra/terraform/environments/aws"
    ENDPOINT_FLAG=""
    ;;
  *)
    echo "modo desconhecido: $MODE (use localstack ou aws)" >&2
    exit 1
    ;;
esac

# Esvazia os buckets antes do destroy, como rede de seguranca. Com force_destroy
# ligado o terraform ja daria conta, mas isso evita surpresa em bucket versionado.
echo ">> esvaziando buckets"
for b in $(terraform -chdir="$ROOT" output -json bucket_names 2>/dev/null | python3 -c "import sys,json;[print(v) for v in json.load(sys.stdin).values()]" 2>/dev/null); do
  echo "   limpando s3://$b"
  aws $ENDPOINT_FLAG s3 rm "s3://$b" --recursive >/dev/null 2>&1 || true
done

echo ">> terraform destroy ($MODE)"
terraform -chdir="$ROOT" destroy -auto-approve

echo ">> ambiente $MODE removido"
