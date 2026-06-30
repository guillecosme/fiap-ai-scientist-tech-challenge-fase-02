# Runbook de execução

Passo a passo para rodar a pipeline localmente, sem custo, e para provisioná-la na AWS de forma agnóstica à conta.

## Execução local (custo zero)

Pré-requisitos: Docker, uv e Java 17 (para o Spark).

```bash
# 1. instalar dependencias
make setup

# 2. rodar a pipeline completa (bronze a gold + gate de qualidade)
bash scripts/run_pipeline_local.sh
```

O script roda, na mesma ordem da Step Functions, a ingestão batch, a ingestão streaming (eventos simulados), a Silver, a Gold e o gate de qualidade. As camadas saem em `data/bronze`, `data/silver` e `data/gold` no formato Parquet.

Sem um projeto de billing do Google Cloud configurado, a ingestão usa as amostras versionadas em `data/seeds`. Para puxar da Base dos Dados de verdade, defina:

```bash
export BD_BILLING_PROJECT_ID="seu-projeto-gcp"
```

### Etapas avulsas

```bash
export STORAGE_BACKEND=local PYTHONPATH=src
RUN="uv run --with pyspark==3.5.3 --with pandas --with pyarrow python"

$RUN jobs/batch_ingest_job.py
$RUN src/pipeline/ingestion/streaming_producer.py --target file --count 120 --ano 2025
$RUN jobs/silver_job.py
$RUN jobs/gold_job.py
$RUN jobs/quality_job.py
```

### Consultar a Gold localmente

```bash
uv run --with duckdb python -c "import duckdb; print(duckdb.sql(\"select * from read_parquet('data/gold/indicador_municipio/**/*.parquet', hive_partitioning=true)\").df())"
```

## Execução local contra o LocalStack

Para exercitar o caminho de nuvem (S3, Kinesis, Lambda) sem conta AWS:

```bash
make up                         # sobe LocalStack e Spark via docker compose
cd infra/terraform/environments/dev
terraform init
terraform apply -var="use_localstack=true"
```

## Provisionamento na AWS

Pré-requisitos: Terraform e credenciais AWS (via `aws configure` ou variáveis de ambiente).

```bash
cd infra/terraform/environments/dev
terraform init
terraform apply
```

O `apply` cria os buckets das três camadas, o catálogo Glue, os jobs, o stream Kinesis e a Lambda, a state machine, a agenda no EventBridge e o monitoramento. Os nomes de bucket recebem um sufixo aleatório, então não há colisão nem dependência de account id.

Para receber alertas por e-mail:

```bash
terraform apply -var="alert_email=voce@exemplo.com"
```

### Rodar a pipeline na AWS

A pipeline dispara sozinha na agenda do EventBridge. Para rodar sob demanda, inicie a state machine pelo console do Step Functions ou pela CLI:

```bash
aws stepfunctions start-execution --state-machine-arn "$(terraform output -raw state_machine_arn)"
```

### Destruir o ambiente

```bash
terraform destroy
```

Tudo que foi criado é removido. É o que permite subir o ambiente na conta do avaliador, demonstrar e derrubar sem deixar custo residual.

## Qualidade e testes

```bash
make lint    # ruff
make test    # pytest (os testes que dependem de Spark pulam sem Java)
```
