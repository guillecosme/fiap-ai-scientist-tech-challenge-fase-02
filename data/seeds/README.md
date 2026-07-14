# Fontes locais (seeds)

Extrato em escala nacional das seis entidades do desafio, usado quando não há
projeto de billing do Google Cloud configurado para consultar a Base dos Dados.
Rodam a pipeline de ponta a ponta localmente, sem credenciais, e alimentam os
testes.

Como são geradas: por [`scripts/preparar_fontes.py`](../../scripts/preparar_fontes.py),
de forma reprodutível (mesma seed, mesmo resultado).

- **Território (uf, municipio): dado real da API pública do IBGE.** 27 UFs e 5.571
  municípios, com nomes e códigos oficiais.
- **Metas e alunos (meta_brasil, meta_uf, meta_municipio, alunos): simulados** no
  mesmo grão e esquema das fontes reais, com um gradiente regional plausível. O
  microdado do Indicador Criança Alfabetizada só é distribuído pela Base dos
  Dados (BigQuery), que exige billing.

Em produção, a ingestão batch puxa as tabelas direto da Base dos Dados (ver
`src/pipeline/ingestion/sources.py`); basta definir `BD_BILLING_PROJECT_ID`.

As chaves são consistentes entre os arquivos (id_uf, id_municipio, sigla_uf, ano)
para que a integração na Silver e os cruzamentos da Gold funcionem. Uma execução
com esses dados e as evidências de volume e custo estão em
[`docs/evidencias_execucao.md`](../../docs/evidencias_execucao.md).
