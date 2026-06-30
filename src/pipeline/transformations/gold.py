"""Transformacoes da camada Gold.

A Gold organiza o dado da Silver em um modelo dimensional simples (uma dimensao
de municipio e uma tabela fato no grao ano x municipio x rede) e em marts prontos
para consumo: o indicador por municipio comparado a meta, a comparacao por UF e a
evolucao temporal. E a camada que alimenta dashboards, analises e modelos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pipeline.common import get_spark, layer_path, read_parquet, write_parquet

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


def _silver(spark: SparkSession, dataset: str) -> DataFrame:
    return read_parquet(spark, layer_path("silver", dataset))


def build_dim_municipio(spark: SparkSession) -> DataFrame:
    municipio = _silver(spark, "municipio")
    uf = _silver(spark, "uf").select("id_uf", "nome_uf", "nome_regiao")
    return municipio.join(uf, on="id_uf", how="left").select(
        "id_municipio",
        "nome_municipio",
        "sigla_uf",
        "id_uf",
        "nome_uf",
        "nome_regiao",
    )


def build_fato_alfabetizacao(spark: SparkSession) -> DataFrame:
    """Fato no grao ano x municipio x rede, com a meta municipal ao lado."""
    from pyspark.sql import functions as F

    alunos = _silver(spark, "alunos")
    meta = _silver(spark, "meta_municipio").select(
        "ano", "id_municipio", F.col("meta_indicador").alias("meta_municipio")
    )
    return (
        alunos.join(meta, on=["ano", "id_municipio"], how="left")
        .withColumn("atingiu_meta", F.col("indicador_pct") >= F.col("meta_municipio"))
        .withColumn("gap_meta_pp", F.round(F.col("indicador_pct") - F.col("meta_municipio"), 1))
        .select(
            "ano",
            "id_municipio",
            "nome_municipio",
            "sigla_uf",
            "id_uf",
            "nome_regiao",
            "rede",
            "qtd_avaliados",
            "qtd_alfabetizados",
            "media_proficiencia",
            "indicador_pct",
            "meta_municipio",
            "atingiu_meta",
            "gap_meta_pp",
        )
    )


def _indicador_municipio_total(spark: SparkSession) -> DataFrame:
    """Indicador consolidado por municipio e ano, somando as redes."""
    from pyspark.sql import functions as F

    alunos = _silver(spark, "alunos")
    return (
        alunos.groupBy("ano", "id_municipio", "nome_municipio", "sigla_uf", "id_uf", "nome_regiao")
        .agg(
            F.sum("qtd_avaliados").alias("qtd_avaliados"),
            F.sum("qtd_alfabetizados").alias("qtd_alfabetizados"),
        )
        .withColumn(
            "indicador_pct",
            F.round(100 * F.col("qtd_alfabetizados") / F.col("qtd_avaliados"), 1),
        )
    )


def build_indicador_municipio(spark: SparkSession) -> DataFrame:
    """Mart: indicador por municipio comparado a meta municipal."""
    from pyspark.sql import functions as F

    total = _indicador_municipio_total(spark)
    meta = _silver(spark, "meta_municipio").select(
        "ano", "id_municipio", F.col("meta_indicador").alias("meta_municipio")
    )
    return (
        total.join(meta, on=["ano", "id_municipio"], how="left")
        .withColumn("atingiu_meta", F.col("indicador_pct") >= F.col("meta_municipio"))
        .withColumn("gap_meta_pp", F.round(F.col("indicador_pct") - F.col("meta_municipio"), 1))
    )


def build_evolucao_temporal(spark: SparkSession) -> DataFrame:
    """Mart: serie do indicador por municipio com variacao ano a ano."""
    from pyspark.sql import Window
    from pyspark.sql import functions as F

    total = _indicador_municipio_total(spark).select(
        "ano", "id_municipio", "nome_municipio", "sigla_uf", "nome_regiao", "indicador_pct"
    )
    janela = Window.partitionBy("id_municipio").orderBy("ano")
    return (
        total.withColumn("indicador_ano_anterior", F.lag("indicador_pct").over(janela))
        .withColumn(
            "variacao_pp",
            F.round(F.col("indicador_pct") - F.col("indicador_ano_anterior"), 1),
        )
        .orderBy("id_municipio", "ano")
    )


def build_comparacao_meta_uf(spark: SparkSession) -> DataFrame:
    """Mart: indicador agregado por UF comparado a meta estadual."""
    from pyspark.sql import functions as F

    total = _indicador_municipio_total(spark)
    por_uf = (
        total.groupBy("ano", "sigla_uf", "nome_regiao")
        .agg(
            F.sum("qtd_avaliados").alias("qtd_avaliados"),
            F.sum("qtd_alfabetizados").alias("qtd_alfabetizados"),
        )
        .withColumn(
            "indicador_pct",
            F.round(100 * F.col("qtd_alfabetizados") / F.col("qtd_avaliados"), 1),
        )
    )
    meta_uf = _silver(spark, "meta_uf").select(
        "ano", "sigla_uf", F.col("meta_indicador").alias("meta_uf")
    )
    return (
        por_uf.join(meta_uf, on=["ano", "sigla_uf"], how="left")
        .withColumn("atingiu_meta", F.col("indicador_pct") >= F.col("meta_uf"))
        .withColumn("gap_meta_pp", F.round(F.col("indicador_pct") - F.col("meta_uf"), 1))
    )


def run() -> None:
    spark = get_spark("gold")

    tabelas = {
        "dim_municipio": build_dim_municipio(spark),
        "fato_alfabetizacao": build_fato_alfabetizacao(spark),
        "indicador_municipio": build_indicador_municipio(spark),
        "evolucao_temporal": build_evolucao_temporal(spark),
        "comparacao_meta_uf": build_comparacao_meta_uf(spark),
    }

    for nome, df in tabelas.items():
        destino = layer_path("gold", nome)
        particoes = ["ano"] if "ano" in df.columns else None
        write_parquet(df, destino, mode="overwrite", partition_by=particoes)
        print(f"[gold] {nome} gravado em {destino}")


if __name__ == "__main__":
    run()
