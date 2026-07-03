"""Resolucao de caminhos e leitura/escrita das camadas em Parquet."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pipeline.common.config import Settings, get_settings

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


def layer_path(layer: str, dataset: str, settings: Settings | None = None) -> str:
    """Caminho base de um dataset dentro de uma camada.

    Em backend local retorna um caminho de filesystem (data/<layer>/<dataset>);
    em S3 retorna s3a://<bucket-da-camada>/<dataset>.
    """
    settings = settings or get_settings()
    if settings.storage_backend == "s3":
        return f"s3a://{settings.bucket(layer)}/{dataset}"
    return f"{settings.data_root}/{layer}/{dataset}"


def write_parquet(
    df: DataFrame,
    path: str,
    mode: str = "overwrite",
    partition_by: list[str] | None = None,
) -> None:
    writer = df.write.mode(mode)
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    writer.parquet(path)


def read_parquet(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.parquet(path)
