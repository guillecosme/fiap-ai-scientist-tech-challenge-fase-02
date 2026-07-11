# FinOps

Como a arquitetura foi pensada para ser eficiente em custo e quais decisões puxam o gasto para baixo.

## Princípios

A ideia central é pagar pelo uso e não por capacidade ociosa. Toda a pipeline é serverless (Glue, Athena, Kinesis on-demand, Lambda, Step Functions), o que significa que, fora das janelas de processamento, o custo de computação tende a zero. Soma-se a isso o fato de o ambiente inteiro ser efêmero: como tudo é provisionado por Terraform, dá para subir, rodar e destruir com `terraform destroy`, sem deixar recurso ligado gerando conta.

## Decisões que reduzem custo

**Parquet em vez de CSV/JSON.** As camadas são gravadas em Parquet, formato colunar e comprimido. Isso reduz o volume armazenado e, principalmente, o volume lido pelas consultas, já que o Athena cobra por byte lido.

**Particionamento por ano e por data de ingestão.** Com as tabelas particionadas, as consultas e os jobs leem só as partições necessárias (partition pruning), em vez de varrer a base inteira. Menos leitura, menos custo.

**Ciclo de vida no S3.** O Bronze, que guarda o histórico bruto e é o que mais cresce, transiciona para Standard-IA aos 30 dias e Glacier aos 120, e tem as versões antigas expiradas aos 90. Silver e Gold ficam quentes por mais tempo, pois são o que alimenta consultas e modelos. Uploads multipart incompletos são abortados após 7 dias.

**Kinesis on-demand.** O stream escala sozinho com o volume e cobra pelo que passa, sem precisar dimensionar e pagar shards reservados.

**Teto de bytes por query no Athena.** O workgroup tem um limite de bytes lidos por consulta, que barra queries acidentais que varreriam dados demais antes de virarem gasto.

**Step Functions e EventBridge no lugar de Airflow gerenciado.** O MWAA cobra por um ambiente que fica de pé o tempo todo, mesmo ocioso (na ordem de algumas centenas de reais por mês). Step Functions e EventBridge são serverless e cobram por execução, o que casa com uma pipeline que roda em janelas. O trade-off está em decisões arquiteturais no README.

**Glue com poucos workers.** Os jobs usam G.1X com 2 workers, suficiente para o volume deste indicador. O dimensionamento pode crescer junto com o dado, sem custo fixo enquanto não cresce.

**Tags em todos os recursos.** Projeto, ambiente e domínio são aplicados como tags padrão, o que permite rastrear o custo por projeto no Cost Explorer e aplicar showback.

## Estimativa de custo

Premissas: volume típico do indicador (dezenas de milhares de municípios e medições, na casa de poucos GB por camada), região us-east-1, valores de referência públicos da AWS. Servem para ordem de grandeza, não como cotação fechada.

| Serviço | Premissa | Custo aproximado |
|---|---|---|
| S3 (3 camadas) | ~10 GB, com lifecycle movendo o frio | US$ 0,20 a 0,40 por mês |
| Glue (4 jobs) | ~3 DPU, ~10 min por job | US$ 0,10 a 0,15 por execução completa |
| Kinesis on-demand | stream ativo na janela de ingestão | US$ 0,04 por hora ativa |
| Lambda (consumer) | dentro do free tier no volume simulado | ~US$ 0,00 |
| Step Functions | poucas transições por execução | centavos por mês |
| Athena | consultas em Parquet particionado | centavos por consulta |
| CloudWatch | 3 alarmes + 1 dashboard | ~US$ 3,50 por mês |

Dois cenários ajudam a ler a tabela:

- **Pipeline rodando uma vez por dia, recursos sempre de pé:** o custo é dominado por Glue e CloudWatch e fica na casa de poucas dezenas de dólares por mês.
- **Ambiente efêmero (sobe, processa e destrói):** o custo cai para a ordem de centavos a poucos dólares por ciclo, e a maior parte do uso cabe no free tier da AWS.

A maior alavanca de custo é a frequência de execução do Glue. Para dado público que atualiza em lotes pouco frequentes, rodar a pipeline sob demanda (ou em cadência semanal/mensal) em vez de diária reduz o gasto de forma significativa, sem perda de valor analítico.

## Como controlar na prática

- Acompanhar custo por tag de projeto no Cost Explorer.
- Manter o teto de bytes do Athena e revisar consultas caras pelo histórico do workgroup.
- Destruir o ambiente quando não estiver em uso (`make destroy`).
- Ajustar a agenda do EventBridge à cadência real de atualização da fonte.
