# Dicionário de dados

Entidades das fontes e das camadas. As chaves são consistentes entre as tabelas (id_uf, id_municipio, sigla_uf, ano), o que sustenta a integração na Silver e os cruzamentos na Gold.

## Fontes (Base dos Dados)

### uf
| Campo | Tipo | Descrição |
|---|---|---|
| id_uf | int | Código IBGE da UF |
| sigla_uf | string | Sigla da UF |
| nome_uf | string | Nome da UF |
| id_regiao | int | Código da região |
| nome_regiao | string | Nome da região |

### municipio
| Campo | Tipo | Descrição |
|---|---|---|
| id_municipio | long | Código IBGE de 7 dígitos |
| nome_municipio | string | Nome do município |
| sigla_uf | string | Sigla da UF |
| id_uf | int | Código da UF |

### meta_brasil
| Campo | Tipo | Descrição |
|---|---|---|
| ano | int | Ano de referência |
| meta_indicador | double | Meta nacional do indicador (percentual) |

### meta_uf
| Campo | Tipo | Descrição |
|---|---|---|
| ano | int | Ano de referência |
| sigla_uf | string | Sigla da UF |
| meta_indicador | double | Meta da UF (percentual) |

### meta_municipio
| Campo | Tipo | Descrição |
|---|---|---|
| ano | int | Ano de referência |
| id_municipio | long | Código do município |
| meta_indicador | double | Meta do município (percentual) |

### alunos
Resultado agregado da avaliação por município e rede. No streaming, chega como eventos de medição com os mesmos campos mais metadados de evento (event_id, event_time, event_type).

| Campo | Tipo | Descrição |
|---|---|---|
| ano | int | Ano da avaliação |
| id_municipio | long | Código do município |
| rede | string | Rede de ensino (publica, privada) |
| qtd_avaliados | long | Quantidade de alunos avaliados |
| qtd_alfabetizados | long | Quantidade que atingiu o corte de 743 no Saeb |
| media_proficiencia | double | Proficiência média na escala Saeb |

## Camada Gold

### dim_municipio
Dimensão de município com atributos de UF e região.

### fato_alfabetizacao
Grão ano x município x rede. Medidas: qtd_avaliados, qtd_alfabetizados (aditivas), media_proficiencia, indicador_pct. Atributos de meta: meta_municipio, atingiu_meta, gap_meta_pp.

### indicador_municipio
Indicador consolidado por município e ano (soma das redes), com meta municipal, atingimento e gap em pontos percentuais.

### comparacao_meta_uf
Indicador agregado por UF e ano contra a meta estadual.

### evolucao_temporal
Série do indicador por município e ano, com o valor do ano anterior e a variação em pontos percentuais.

## Campos derivados

- **indicador_pct**: `100 * qtd_alfabetizados / qtd_avaliados`. Percentual de crianças alfabetizadas.
- **atingiu_meta**: verdadeiro quando `indicador_pct >= meta`.
- **gap_meta_pp**: `indicador_pct - meta`, a distância para a meta em pontos percentuais.
