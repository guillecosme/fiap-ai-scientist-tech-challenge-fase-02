# Exemplos de consulta na camada Gold

Consultas de exemplo sobre a Gold, mostrando que a camada está pronta para dashboards, análise e preparação de dados para machine learning. As consultas estão em SQL no padrão do Athena (tabelas registradas pelo crawler no Glue Data Catalog). Para rodar localmente, aponte o DuckDB para os arquivos Parquet em `data/gold`, como no final deste documento.

## Indicador por município

```sql
select nome_municipio, sigla_uf, indicador_pct, meta_municipio, gap_meta_pp
from gold.indicador_municipio
where ano = 2025
order by indicador_pct desc;
```

## Municípios mais distantes da meta

Útil para priorizar onde concentrar esforço.

```sql
select nome_municipio, sigla_uf, indicador_pct, meta_municipio, gap_meta_pp
from gold.indicador_municipio
where ano = 2025 and gap_meta_pp < 0
order by gap_meta_pp asc;
```

## Comparação entre meta e resultado por UF

```sql
select sigla_uf, nome_regiao, indicador_pct, meta_uf, atingiu_meta, gap_meta_pp
from gold.comparacao_meta_uf
where ano = 2025
order by indicador_pct desc;
```

## Evolução temporal do indicador

```sql
select ano, nome_municipio, indicador_pct, indicador_ano_anterior, variacao_pp
from gold.evolucao_temporal
where nome_municipio = 'Salvador'
order by ano;
```

## Diferença entre redes pública e privada

Sobre a tabela fato, no grão município x rede.

```sql
select nome_municipio, sigla_uf, rede, indicador_pct
from gold.fato_alfabetizacao
where ano = 2025
order by nome_municipio, rede;
```

## Tabela de atributos para machine learning

Monta uma base por município e ano, cruzando indicador, meta, gap e variação, pronta para treinar um modelo de predição do indicador ou de risco de não atingir a meta.

```sql
select
  i.ano,
  i.id_municipio,
  i.nome_regiao,
  i.indicador_pct,
  i.meta_municipio,
  i.gap_meta_pp,
  e.variacao_pp
from gold.indicador_municipio i
left join gold.evolucao_temporal e
  on i.ano = e.ano and i.id_municipio = e.id_municipio
where i.ano = 2025;
```

Enriquecida com fontes externas (Censo Escolar, IBGE, Atlas do Desenvolvimento Humano), essa base vira o ponto de partida para os modelos descritos na seção de aplicação em IA do README.

## Rodando localmente com DuckDB

```bash
uv run --with duckdb python - <<'PY'
import duckdb
con = duckdb.connect()
print(con.sql("""
  select nome_municipio, sigla_uf, indicador_pct, gap_meta_pp
  from read_parquet('data/gold/indicador_municipio/**/*.parquet', hive_partitioning=true)
  where ano = 2025
  order by gap_meta_pp asc
""").df())
PY
```
