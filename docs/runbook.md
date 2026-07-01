# Runbook de execução

Referência rápida de comandos. O guia com a tabela de decisão e a saída esperada de cada passo está em [deploy.md](deploy.md).

Antes de tudo, cheque os pré-requisitos:

```bash
make doctor
```

## Modo local (custo zero)

Pré-requisitos: uv e Java 17.

```bash
make setup
make local
```

Roda a pipeline inteira (ingestão batch, streaming em arquivo, Silver, Gold e o gate de qualidade). As camadas saem em `data/` em Parquet.

Sem um projeto de billing do Google Cloud, a ingestão usa as amostras de `data/seeds`. Para puxar da Base dos Dados, defina `BD_BILLING_PROJECT_ID` no `.env`.

Consultar a Gold localmente:

```bash
uv run --with duckdb python -c "import duckdb; print(duckdb.sql(\"select * from read_parquet('data/gold/indicador_municipio/**/*.parquet', hive_partitioning=true)\").df())"
```

## Modo LocalStack

```bash
make ls-up          # sobe LocalStack e Spark
make ls-deploy      # provisiona a infra e imprime as variaveis do .env
# copie as variaveis para o .env
make ls-run         # roda a pipeline contra o S3 do LocalStack
make ls-destroy     # esvazia buckets e destroi
make ls-down        # derruba os containers
```

## Modo AWS real

Pré-requisitos: Terraform e credenciais AWS (confirme com `aws sts get-caller-identity`).

```bash
cd infra/terraform/environments/aws
cp example.tfvars terraform.tfvars     # ajuste project, region e alert_email
cd -
make aws-deploy     # provisiona todo o ambiente
make aws-run        # dispara a pipeline (Step Functions)
make aws-destroy    # esvazia buckets e destroi
```

Os nomes de bucket recebem um sufixo aleatório, então o ambiente sobe e desce em qualquer conta sem ajuste manual. O `force_destroy` e o `teardown` esvaziam os buckets antes do destroy, evitando travar em bucket não vazio.

## Qualidade e testes

```bash
make lint    # ruff
make test    # pytest (os testes que dependem de Spark pulam sem Java)
```
