"""Transformacoes da camada Silver.

A Silver pega o dado bruto do Bronze e entrega versoes limpas, padronizadas e ja
integradas: nomes e tipos consistentes, chaves normalizadas, nulos tratados e a
juncao das bases heterogeneas. O destaque e a tabela de alunos integrada, que
unifica a carga batch com os eventos de streaming no mesmo grao.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pipeline.common import get_spark, layer_path, read_parquet, write_parquet

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession

# Colunas tecnicas adicionadas na ingestao, descartadas ao subir para a Silver.
_BRONZE_META = ["ingested_at", "source_table"]


def _drop_bronze_meta(df: DataFrame) -> DataFrame:
    existentes = [c for c in _BRONZE_META if c in df.columns]
    return df.drop(*existentes) if existentes else df


def clean_uf(spark: SparkSession) -> DataFrame:
    from pyspark.sql import functions as F

    df = _drop_bronze_meta(read_parquet(spark, layer_path("bronze", "uf")))
    return (
        df.withColumn("id_uf", F.col("id_uf").cast("int"))
        .withColumn("sigla_uf", F.upper(F.trim(F.col("sigla_uf"))))
        .withColumn("nome_uf", F.trim(F.col("nome_uf")))
        .withColumn("nome_regiao", F.trim(F.col("nome_regiao")))
        .dropna(subset=["id_uf", "sigla_uf"])
        .dropDuplicates(["id_uf"])
    )


def clean_municipio(spark: SparkSession) -> DataFrame:
    from pyspark.sql import functions as F

    df = _drop_bronze_meta(read_parquet(spark, layer_path("bronze", "municipio")))
    return (
        df.withColumn("id_municipio", F.col("id_municipio").cast("long"))
        .withColumn("id_uf", F.col("id_uf").cast("int"))
        .withColumn("sigla_uf", F.upper(F.trim(F.col("sigla_uf"))))
        .withColumn("nome_municipio", F.trim(F.col("nome_municipio")))
        .dropna(subset=["id_municipio"])
        .dropDuplicates(["id_municipio"])
    )


def clean_meta(spark: SparkSession, dataset: str, keys: list[str]) -> DataFrame:
    from pyspark.sql import functions as F

    df = _drop_bronze_meta(read_parquet(spark, layer_path("bronze", dataset)))
    df = df.withColumn("ano", F.col("ano").cast("int")).withColumn(
        "meta_indicador", F.col("meta_indicador").cast("double")
    )
    if "sigla_uf" in df.columns:
        df = df.withColumn("sigla_uf", F.upper(F.trim(F.col("sigla_uf"))))
    if "id_municipio" in df.columns:
        df = df.withColumn("id_municipio", F.col("id_municipio").cast("long"))
    return df.dropna(subset=keys).dropDuplicates(keys)


def _read_streaming_alunos(spark: SparkSession) -> DataFrame | None:
    """Le os eventos de alunos vindos do streaming, se existirem."""
    from pyspark.sql import functions as F

    path = layer_path("bronze", "alunos_streaming")
    # Em backend local da para checar a existencia; em S3 confiamos no read.
    if not path.startswith("s3a://") and not os.path.exists(path):
        return None
    try:
        eventos = spark.read.json(path)
    except Exception:
        return None
    if "id_municipio" not in eventos.columns:
        return None
    return eventos.select(
        F.col("ano").cast("int").alias("ano"),
        F.col("id_municipio").cast("long").alias("id_municipio"),
        F.lower(F.trim(F.col("rede"))).alias("rede"),
        F.col("qtd_avaliados").cast("long").alias("qtd_avaliados"),
        F.col("qtd_alfabetizados").cast("long").alias("qtd_alfabetizados"),
        F.col("media_proficiencia").cast("double").alias("media_proficiencia"),
    )


def _read_batch_alunos(spark: SparkSession) -> DataFrame:
    from pyspark.sql import functions as F

    df = _drop_bronze_meta(read_parquet(spark, layer_path("bronze", "alunos")))
    return df.select(
        F.col("ano").cast("int").alias("ano"),
        F.col("id_municipio").cast("long").alias("id_municipio"),
        F.lower(F.trim(F.col("rede"))).alias("rede"),
        F.col("qtd_avaliados").cast("long").alias("qtd_avaliados"),
        F.col("qtd_alfabetizados").cast("long").alias("qtd_alfabetizados"),
        F.col("media_proficiencia").cast("double").alias("media_proficiencia"),
    )


def build_alunos_integrado(spark: SparkSession) -> DataFrame:
    """Integra alunos de batch e streaming e enriquece com municipio e UF.

    Como o streaming traz medicoes individuais e o batch traz agregados, tudo e
    reagrupado no grao ano + municipio + rede: as quantidades sao somadas e a
    proficiencia vira media ponderada pelo numero de avaliados.
    """
    from pyspark.sql import functions as F

    batch = _read_batch_alunos(spark)
    streaming = _read_streaming_alunos(spark)
    base = batch.unionByName(streaming) if streaming is not None else batch

    agregado = (
        base.dropna(subset=["ano", "id_municipio", "rede"])
        .withColumn("prof_peso", F.col("media_proficiencia") * F.col("qtd_avaliados"))
        .groupBy("ano", "id_municipio", "rede")
        .agg(
            F.sum("qtd_avaliados").alias("qtd_avaliados"),
            F.sum("qtd_alfabetizados").alias("qtd_alfabetizados"),
            F.sum("prof_peso").alias("prof_peso"),
        )
        .withColumn(
            "media_proficiencia",
            F.round(F.col("prof_peso") / F.col("qtd_avaliados"), 1),
        )
        .withColumn(
            "indicador_pct",
            F.round(100 * F.col("qtd_alfabetizados") / F.col("qtd_avaliados"), 1),
        )
        .drop("prof_peso")
    )

    municipios = clean_municipio(spark).select(
        "id_municipio", "nome_municipio", "sigla_uf", "id_uf"
    )
    ufs = clean_uf(spark).select("id_uf", "nome_uf", "nome_regiao")

    return (
        agregado.join(municipios, on="id_municipio", how="left")
        .join(ufs, on="id_uf", how="left")
        .select(
            "ano",
            "id_municipio",
            "nome_municipio",
            "sigla_uf",
            "id_uf",
            "nome_uf",
            "nome_regiao",
            "rede",
            "qtd_avaliados",
            "qtd_alfabetizados",
            "media_proficiencia",
            "indicador_pct",
        )
    )


def run() -> None:
    spark = get_spark("silver")

    tabelas = {
        "uf": clean_uf(spark),
        "municipio": clean_municipio(spark),
        "meta_brasil": clean_meta(spark, "meta_brasil", ["ano"]),
        "meta_uf": clean_meta(spark, "meta_uf", ["ano", "sigla_uf"]),
        "meta_municipio": clean_meta(spark, "meta_municipio", ["ano", "id_municipio"]),
        "alunos": build_alunos_integrado(spark),
    }

    for nome, df in tabelas.items():
        destino = layer_path("silver", nome)
        particoes = ["ano"] if "ano" in df.columns else None
        write_parquet(df, destino, mode="overwrite", partition_by=particoes)
        print(f"[silver] {nome} gravado em {destino}")


if __name__ == "__main__":
    run()
