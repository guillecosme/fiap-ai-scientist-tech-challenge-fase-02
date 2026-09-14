# Evidências de execução

Registro de uma execução real da pipeline de ponta a ponta, com o volume de todos os municípios do Brasil, e a leitura de custo que ela implica.

## Origem dos dados

- **Território (UF e município): dado real da API pública do IBGE**, sem login e sem custo. 27 UFs e 5.571 municípios, com nomes e códigos oficiais. O enunciado lista o IBGE como fonte de território.
- **Metas e alunos: extratos reais do Inep.** As metas nacional, por UF e por município (2024 a 2030) vêm das planilhas de resultados e metas que o Inep publica desde 2023, no formato largo da fonte (uma coluna por ano), convertido para o formato longo; os dados de alunos vêm dos microdados da avaliação da alfabetização (2024 e 2025), agregados no grão ano x município x rede reproduzindo o cálculo oficial (média ponderada pelo peso amostral entre presentes com prova preenchida). A extração está em [scripts/extrair_inep.py](../scripts/extrair_inep.py) e é acionada por [scripts/preparar_fontes.py](../scripts/preparar_fontes.py). Na primeira versão da pipeline esses quatro conjuntos eram simulados, porque o microdado só saía pela Base dos Dados (BigQuery com billing); a simulação continua disponível com `--simulado`, para uso offline.
- O caminho de leitura real do BigQuery existe no código, em [batch_ingest.py](../src/pipeline/ingestion/batch_ingest.py) (`_read_from_base_dos_dados`), e é acionado quando `BD_BILLING_PROJECT_ID` está definido.

## Execução

Ambiente: Spark em modo local (backend de filesystem), o mesmo código que roda como job Glue na AWS. Data de ingestão `2026-07-13`, com o extrato daquela versão (território real, metas e alunos simulados). Os volumes abaixo são os dessa execução medida; a seção seguinte registra o extrato real que substituiu a simulação em setembro de 2026. Tempo total das quatro etapas (ingestão batch, Silver, Gold e gate de qualidade): cerca de 32 segundos.

### Volume por camada (medido)

| Camada | Tabela | Linhas | Partições | Tamanho Parquet |
|---|---|---:|---:|---:|
| Bronze | uf | 27 | por data | 424 KB (camada) |
| Bronze | municipio | 5.571 | por data | |
| Bronze | meta_brasil | 3 | por data | |
| Bronze | meta_uf | 54 | por data | |
| Bronze | meta_municipio | 11.142 | por data | |
| Bronze | alunos | 15.036 | por data | |
| Silver | alunos (integrada) | 15.036 | 2 (ano) | 716 KB (camada) |
| Silver | meta_municipio | 11.142 | 2 (ano) | |
| Gold | dim_municipio | 5.571 | 1 | 1,2 MB (camada) |
| Gold | fato_alfabetizacao | 15.036 | 2 (ano) | |
| Gold | indicador_municipio | 11.142 | 2 (ano) | |
| Gold | evolucao_temporal | 11.142 | 2 (ano) | |
| Gold | comparacao_meta_uf | 54 | 2 (ano) | |

Lake completo nas três camadas: cerca de 2,3 MB em Parquet comprimido.

### Extrato real (setembro de 2026)

Com a publicação dos microdados pelo Inep, o extrato de `data/seeds` passou a ser real nas seis entidades. Volumes do extrato, no mesmo esquema que a ingestão batch lê:

| Entidade | Linhas | Origem |
|---|---:|---|
| uf | 27 | API do IBGE |
| municipio | 5.571 | API do IBGE |
| meta_brasil | 7 | planilhas de resultados e metas do Inep (2024 a 2030) |
| meta_uf | 175 | idem, por UF |
| meta_municipio | 38.290 | idem, por município (5.470 municípios com trajetória completa) |
| alunos | 13.110 | microdados 2024 e 2025 agregados por ano, município e rede (3,8 milhões de alunos avaliados) |

O percentual de alfabetizados calculado do agregado (`qtd_alfabetizados / qtd_avaliados`) reproduz o número oficial publicado por município com diferença média de 0,03 ponto percentual. As etapas da pipeline não mudaram; só a origem do dado.

### Gate de qualidade

As 11 checagens rodaram sobre a Silver e a Gold e **todas passaram** (duplicidade, valores ausentes, integridade referencial de alunos e metas com município e UF, faixa de 0 a 100 do indicador e consistência de alfabetizados menor ou igual a avaliados). Nenhuma falha crítica, promoção liberada.

### Recorte analítico da Gold (2025)

Média do indicador por região, sobre os 5.571 municípios, direto do mart `indicador_municipio`:

| Região | Indicador médio | Municípios | Atingiram a meta |
|---|---:|---:|---:|
| Sul | 80,2% | 1.191 | 37% |
| Sudeste | 76,0% | 1.668 | 42% |
| Centro-Oeste | 72,0% | 468 | 38% |
| Nordeste | 61,1% | 1.794 | 32% |
| Norte | 59,2% | 450 | 26% |
| **Brasil** | **70,4%** | **5.571** | **36%** |

É exatamente a desigualdade territorial que o indicador existe para revelar, e que a camada Gold entrega pronta para consumo.

## Evidência de custo

### Fonte (BigQuery / Base dos Dados)

O BigQuery cobra por bytes lidos na consulta. As tabelas de referência e metas do Indicador somam poucas dezenas de MB por leitura completa. A franquia é de **1 TB por mês gratuito**; acima disso, o on-demand custa cerca de US$ 6,25 por TB. Uma ingestão mensal que lê algumas dezenas de MB fica inteira dentro da franquia, então o **custo de leitura da fonte é R$ 0**. É a estimativa do custo da query real; a medição exata (bytes faturados) exige um projeto de billing, que não temos aqui.

### Pipeline na AWS (mapeado do volume medido)

| Item | Base | Custo |
|---|---|---|
| S3 (3 camadas) | ~2,3 MB, com lifecycle no Bronze frio | fração de centavo por mês |
| Glue | ~2 workers G.1X, poucos minutos por execução | US$ 0,10 a 0,15 por execução |
| Athena | Parquet particionado, KB a MB por consulta | centavos por consulta |
| CloudWatch | 3 alarmes + 1 dashboard | ~US$ 3,50 por mês |

No volume real do indicador, o custo é dominado por CloudWatch e Glue: poucas dezenas de reais por mês com tudo de pé, ou centavos por ciclo no modo efêmero (sobe, processa e destrói). O detalhamento completo está em [finops.md](finops.md).

## Como reproduzir

```bash
python scripts/preparar_fontes.py --out data/seeds   # baixa o território do IBGE e os arquivos do Inep e gera o extrato
make local                                            # roda a pipeline no filesystem e o gate de qualidade
```

Para o caminho de nuvem, `make ls-*` roda contra o LocalStack e `make aws-*` contra uma conta AWS real. Para ler a fonte de verdade no BigQuery, basta exportar `BD_BILLING_PROJECT_ID` com um projeto de billing do Google Cloud.
