#!/usr/bin/env bash
# Roda a pipeline no modo escolhido.
#   local       camadas em data/, Spark local, streaming em arquivo
#   localstack  camadas no S3 do LocalStack, Spark local, streaming via Kinesis
#   aws         dispara a Step Functions (Glue) na conta AWS real
#
# Uso: bash scripts/run_pipeline.sh [local|localstack|aws]
set -euo pipefail

cd "$(dirname "$0")/.."
MODE="${1:-local}"

# carrega .env se existir
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

export PYTHONPATH="src"
RUN="uv run --with pyspark==3.5.3 --with pandas --with pyarrow python"

run_local_chain() {
  local stream_flag="$1"
  echo ">> ingestao batch"
  $RUN jobs/batch_ingest_job.py
  echo ">> ingestao streaming"
  eval "$RUN src/pipeline/ingestion/streaming_producer.py $stream_flag"
  echo ">> camada silver"
  $RUN jobs/silver_job.py
  echo ">> camada gold"
  $RUN jobs/gold_job.py
  echo ">> gate de qualidade"
  $RUN jobs/quality_job.py
}

case "$MODE" in
  local)
    export STORAGE_BACKEND=local
    run_local_chain "--target file --count 120 --ano 2025"
    ;;

  localstack)
    export STORAGE_BACKEND=s3
    export AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-http://localhost:4566}"
    export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
    export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
    STREAM="${KINESIS_STREAM:-$(terraform -chdir=infra/terraform/environments/localstack output -raw kinesis_stream_name 2>/dev/null || echo alfabetizacao-eventos-local)}"
    run_local_chain "--target kinesis --stream $STREAM --endpoint-url $AWS_ENDPOINT_URL --count 120 --ano 2025"
    ;;

  aws)
    ARN="$(terraform -chdir=infra/terraform/environments/aws output -raw state_machine_arn)"
    echo ">> disparando a pipeline na AWS (Step Functions)"
    echo "   state machine: $ARN"
    aws stepfunctions start-execution --state-machine-arn "$ARN"
    echo ">> acompanhe a execucao no console do Step Functions"
    ;;

  *)
    echo "modo desconhecido: $MODE (use local, localstack ou aws)" >&2
    exit 1
    ;;
esac

echo ">> concluido (modo $MODE)"
