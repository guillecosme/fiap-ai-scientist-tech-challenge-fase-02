# FinOps

Decisões de eficiência de custo da arquitetura. Detalhamento e estimativa de custo entram na entrega de FinOps.

## Princípios

- Armazenamento em Parquet com particionamento para reduzir volume e leitura.
- Serviços serverless (Glue, Athena, Kinesis on-demand, Lambda) para pagar pelo uso.
- Ciclo de vida do S3 movendo dados frios para camadas mais baratas.
- Recursos efêmeros e destruição completa via Terraform.

## Estimativa de custo

A detalhar.
