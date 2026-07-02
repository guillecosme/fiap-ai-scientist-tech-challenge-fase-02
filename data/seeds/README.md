# Amostras locais (seeds)

Recortes pequenos e representativos das seis entidades do desafio, usados quando
nao ha projeto de billing do Google Cloud configurado para consultar a Base dos
Dados. Servem para rodar a pipeline de ponta a ponta localmente, sem credenciais,
e para os testes.

Não são o dado oficial completo. Em produção, a ingestão batch puxa as tabelas
direto da Base dos Dados (ver `src/pipeline/ingestion/sources.py`); basta definir
a variável de ambiente `BD_BILLING_PROJECT_ID`.

As chaves são consistentes entre os arquivos (id_uf, id_municipio, sigla_uf, ano)
para que a integração na camada Silver e os cruzamentos da Gold funcionem.
