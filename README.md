# Pipeline Híbrido de Alfabetização no Brasil

Projeto da Fase 2 do MBA em AI Scientist (FIAP / POSTECH). A proposta é construir uma pipeline de dados híbrida, batch e streaming, que integra as fontes públicas do Indicador Criança Alfabetizada e entrega uma camada analítica confiável para apoiar políticas públicas de educação.

O repositório está em construção. Esta versão traz a estrutura inicial e as decisões de arquitetura. As seções abaixo vão sendo preenchidas conforme cada parte da pipeline é implementada, e o detalhamento completo entra na reta final do projeto.

## Contexto

A alfabetização ao final do 2º ano do ensino fundamental é um marco do desenvolvimento educacional. O Compromisso Nacional Criança Alfabetizada mobiliza União, estados e municípios para garantir esse direito, e o Inep definiu em 2023 o corte de 743 pontos na escala Saeb como referência para considerar uma criança alfabetizada. A partir desse parâmetro nasce o Indicador Criança Alfabetizada, que mede o percentual de estudantes que atingem esse patamar.

Entender o que move esse indicador exige cruzar fontes diferentes, de metas nacionais e estaduais a dados territoriais e de desempenho. É esse cruzamento que a pipeline aqui proposta organiza.

## Arquitetura

Solução serverless na AWS, em arquitetura medalhão (Bronze, Silver, Gold), provisionada por Terraform de forma agnóstica à conta. O detalhamento, o diagrama e o fluxo de dados entram nas próximas entregas. Visão resumida:

- Ingestão batch das tabelas de referência e metas a partir da plataforma Base dos Dados.
- Ingestão streaming de eventos simulados (novas medições e atualizações de metas) via Kinesis.
- Camadas Bronze, Silver e Gold em S3, no formato Parquet particionado.
- Processamento com PySpark no AWS Glue.
- Camada analítica consultável via Athena.
- Orquestração com Step Functions, monitoramento com CloudWatch e práticas de FinOps no uso da nuvem.

## Como rodar

A pipeline roda localmente, sem custo, usando LocalStack para emular a AWS, e também na nuvem real via Terraform. O passo a passo completo entra no runbook (`docs/runbook.md`) ao longo do desenvolvimento. Pré-requisitos: Docker, uv e Terraform.

```bash
# instalar dependencias
make setup

# subir ambiente local (LocalStack + Spark)
make up
```

## Estrutura do repositório

```
.
├── infra/terraform/     # infraestrutura como codigo (AWS)
├── src/pipeline/        # ingestao, transformacoes, qualidade e utilitarios
├── jobs/                # entrypoints dos jobs de processamento
├── tests/               # testes
├── docs/                # documentacao tecnica e diagramas
└── data/                # camadas locais (geradas em execucao, nao versionadas)
```

## Documentação

- [Arquitetura](docs/architecture.md)
- [Dicionário de dados](docs/data_dictionary.md)
- [FinOps](docs/finops.md)
- [Runbook de execução](docs/runbook.md)
