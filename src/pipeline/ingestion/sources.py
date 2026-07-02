"""Catalogo das fontes que alimentam a camada Bronze.

As entidades seguem o desafio: UF, Municipio, Meta de Alfabetizacao (Brasil, por
UF e por Municipio) e Dados de alunos. UF e Municipio vem dos diretorios oficiais
da Base dos Dados; as metas e os dados de alunos vem do dataset do Indicador
Crianca Alfabetizada.

Os identificadores de dataset e tabela seguem o padrao da Base dos Dados e podem
precisar de ajuste fino conforme a publicacao da fonte. Quando nao ha projeto de
billing do Google Cloud configurado, a ingestao usa as amostras versionadas em
data/seeds, o que mantem a pipeline rodavel de ponta a ponta sem credenciais.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceTable:
    name: str
    bd_dataset_id: str
    bd_table_id: str
    seed_file: str
    description: str


BATCH_TABLES: tuple[SourceTable, ...] = (
    SourceTable(
        name="uf",
        bd_dataset_id="br_bd_diretorios_brasil",
        bd_table_id="uf",
        seed_file="uf.csv",
        description="Unidades da federacao e suas regioes",
    ),
    SourceTable(
        name="municipio",
        bd_dataset_id="br_bd_diretorios_brasil",
        bd_table_id="municipio",
        seed_file="municipio.csv",
        description="Municipios brasileiros e vinculo com a UF",
    ),
    SourceTable(
        name="meta_brasil",
        bd_dataset_id="br_inep_indicador_crianca_alfabetizada",
        bd_table_id="meta_brasil",
        seed_file="meta_brasil.csv",
        description="Meta nacional do indicador de alfabetizacao por ano",
    ),
    SourceTable(
        name="meta_uf",
        bd_dataset_id="br_inep_indicador_crianca_alfabetizada",
        bd_table_id="meta_uf",
        seed_file="meta_uf.csv",
        description="Meta do indicador por UF e ano",
    ),
    SourceTable(
        name="meta_municipio",
        bd_dataset_id="br_inep_indicador_crianca_alfabetizada",
        bd_table_id="meta_municipio",
        seed_file="meta_municipio.csv",
        description="Meta do indicador por municipio e ano",
    ),
    SourceTable(
        name="alunos",
        bd_dataset_id="br_inep_indicador_crianca_alfabetizada",
        bd_table_id="alunos",
        seed_file="alunos.csv",
        description="Resultado agregado da avaliacao de alfabetizacao por municipio e rede",
    ),
)


def get_batch_table(name: str) -> SourceTable:
    for table in BATCH_TABLES:
        if table.name == name:
            return table
    raise KeyError(f"Tabela batch desconhecida: {name}")
