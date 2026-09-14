# Fontes locais (seeds)

Extrato em escala nacional das seis entidades do desafio, usado quando não há
projeto de billing do Google Cloud configurado para consultar a Base dos Dados.
Rodam a pipeline de ponta a ponta localmente, sem credenciais, e alimentam os
testes.

Como são geradas: por [`scripts/preparar_fontes.py`](../../scripts/preparar_fontes.py),
que baixa o território do IBGE e os arquivos do Inep (via
[`scripts/extrair_inep.py`](../../scripts/extrair_inep.py)).

- **Território (uf, municipio): dado real da API pública do IBGE.** 27 UFs e 5.571
  municípios, com nomes e códigos oficiais.
- **Metas (meta_brasil, meta_uf, meta_municipio): extratos reais do Inep.** Trajetória
  2024 a 2030 de cada unidade, das planilhas de resultados e metas (2023 a 2025),
  convertidas do formato largo da fonte para o formato longo.
- **Alunos: extrato real dos microdados do Inep (2024 e 2025)**, agregado no grão
  ano x município x rede, reproduzindo o cálculo oficial do percentual (ponderado
  pelo peso amostral entre presentes com prova preenchida). As redes são municipal,
  estadual e privada.

A primeira versão simulava metas e alunos, porque o microdado só saía pela Base dos
Dados (BigQuery com billing); a simulação continua disponível com `--simulado`.
Os arquivos brutos do Inep ficam em `data/fontes_inep` (fora do git).

Em produção, a ingestão batch puxa as tabelas direto da Base dos Dados (ver
`src/pipeline/ingestion/sources.py`); basta definir `BD_BILLING_PROJECT_ID`.

As chaves são consistentes entre os arquivos (id_uf, id_municipio, sigla_uf, ano)
para que a integração na Silver e os cruzamentos da Gold funcionem. Uma execução
com esses dados e as evidências de volume e custo estão em
[`docs/evidencias_execucao.md`](../../docs/evidencias_execucao.md).
