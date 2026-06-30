# Arquitetura

Documento de arquitetura da pipeline. Conteúdo detalhado (diagrama, fluxo de dados, decisões e trade-offs) entra ao longo do desenvolvimento, na entrega de documentação.

## Visão geral

Pipeline híbrida (batch + streaming) em arquitetura medalhão sobre AWS, provisionada por Terraform de forma agnóstica à conta.

## Camadas

- Bronze: dados brutos, sem transformação significativa, histórico preservado.
- Silver: dados limpos, padronizados e integrados.
- Gold: datasets analíticos prontos para dashboards, estatística e machine learning.

## Decisões e trade-offs

A detalhar: batch vs streaming, data lake vs data warehouse, custo vs performance, Step Functions vs Airflow.
