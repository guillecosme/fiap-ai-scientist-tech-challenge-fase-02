# Arquitetura

Detalhamento técnico da pipeline. A visão geral, o diagrama e os trade-offs principais estão no [README](../README.md); aqui o foco é como as peças se encaixam por dentro.

## Camadas e responsabilidades

| Camada | Conteúdo | Transformações | Formato |
|---|---|---|---|
| Bronze | Dado bruto das fontes | Nenhuma significativa, só metadados de ingestão | Parquet, particionado por data de ingestão |
| Silver | Dado limpo e integrado | Limpeza, tipos, nulos, normalização de chaves, junção das bases | Parquet, particionado por ano |
| Gold | Dado analítico | Modelo dimensional e marts agregados | Parquet, particionado por ano |

## Componentes

- **Ingestão batch** (`src/pipeline/ingestion/batch_ingest.py`): lê as fontes de referência e metas e grava no Bronze. Roda como job Glue na AWS.
- **Ingestão streaming** (`streaming_producer.py` e `streaming_consumer.py`): produtor publica eventos no Kinesis; a Lambda consome e grava no Bronze.
- **Transformações** (`src/pipeline/transformations/`): `silver.py` e `gold.py`, em PySpark.
- **Qualidade** (`src/pipeline/quality/`): checagens e gate que interrompe a pipeline em falha crítica.
- **Comuns** (`src/pipeline/common/`): configuração por ambiente, sessão Spark, IO das camadas, métricas e a ponte de configuração do Glue.
- **Infra** (`infra/terraform/`): módulos de storage, IAM, streaming, analytics, orquestração e monitoramento, montados em dois roots (`environments/aws` para a conta real e `environments/localstack` para o modo local).

## Backends de armazenamento

A configuração (`pipeline.common.config`) escolhe o backend em tempo de execução:

- `local`: as camadas vivem em diretórios Parquet sob `data/`. Sem credencial, ideal para dev e para o avaliador.
- `s3`: as camadas vivem nos buckets provisionados pelo Terraform. Os nomes chegam por variável de ambiente, já que recebem um sufixo aleatório para serem agnósticos à conta.

O mesmo código PySpark roda nos dois backends; só muda o esquema do caminho (`data/...` ou `s3a://...`).

## Modelo dimensional da Gold

- `dim_municipio`: município com UF e região.
- `fato_alfabetizacao`: grão ano x município x rede, com quantidades aditivas, proficiência, indicador, meta municipal, atingimento e gap.
- `indicador_municipio`: indicador consolidado por município (soma das redes) contra a meta.
- `comparacao_meta_uf`: indicador agregado por UF contra a meta estadual.
- `evolucao_temporal`: série do indicador por município com variação ano a ano.

## Integração das bases

A reconciliação entre batch e streaming acontece na Silver. Os eventos de streaming trazem medições individuais e a carga batch traz agregados; ambos são levados ao grão ano x município x rede, com as quantidades somadas e a proficiência como média ponderada pelo número de avaliados. Em seguida, a junção com município e UF traz os atributos territoriais.

## Decisões e trade-offs

Os trade-offs de batch vs streaming, data lake vs data warehouse e custo vs performance estão descritos no README. Em resumo: híbrido porque cada dado pede um regime; data lake em Parquet porque mantém custo baixo e abre a Gold para SQL e ML; serverless e Step Functions no lugar de MWAA por custo quase zero quando ocioso.
