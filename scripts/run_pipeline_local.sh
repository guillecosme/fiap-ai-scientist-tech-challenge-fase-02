#!/usr/bin/env bash
# Orquestracao local da pipeline completa, na mesma ordem que a Step Functions
# executa na AWS: ingestao batch, ingestao streaming, silver, gold e o gate de
# qualidade. Util para rodar e validar tudo de ponta a ponta sem nuvem.
#
# Uso:
#   bash scripts/run_pipeline_local.sh
#
# Requer Java (para o Spark) e uv. As camadas saem em data/ (backend local).
set -euo pipefail

cd "$(dirname "$0")/.."

export STORAGE_BACKEND="${STORAGE_BACKEND:-local}"
export PYTHONPATH="src"

RUN="uv run --with pyspark==3.5.3 --with pandas --with pyarrow python"

echo ">> 1/5 ingestao batch"
$RUN jobs/batch_ingest_job.py

echo ">> 2/5 ingestao streaming (eventos simulados para o bronze)"
$RUN src/pipeline/ingestion/streaming_producer.py --target file --count 120 --ano 2025

echo ">> 3/5 camada silver"
$RUN jobs/silver_job.py

echo ">> 4/5 camada gold"
$RUN jobs/gold_job.py

echo ">> 5/5 gate de qualidade"
$RUN jobs/quality_job.py

echo ">> pipeline concluida"
