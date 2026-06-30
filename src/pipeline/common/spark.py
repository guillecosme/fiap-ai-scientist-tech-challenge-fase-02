"""Criacao da SparkSession usada pelos jobs de transformacao."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pipeline.common.config import Settings, get_settings

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


def get_spark(app_name: str, settings: Settings | None = None) -> SparkSession:
    from pyspark.sql import SparkSession

    settings = settings or get_settings()
    builder = SparkSession.builder.appName(app_name)

    # Quando o backend e S3, configura o conector s3a. Apontando para o
    # LocalStack, da para exercitar o caminho de nuvem localmente.
    if settings.storage_backend == "s3":
        builder = builder.config(
            "spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"
        ).config("spark.hadoop.fs.s3a.path.style.access", "true")
        if settings.use_localstack:
            builder = (
                builder.config("spark.hadoop.fs.s3a.endpoint", settings.localstack_endpoint)
                .config("spark.hadoop.fs.s3a.access.key", "test")
                .config("spark.hadoop.fs.s3a.secret.key", "test")
            )

    return builder.getOrCreate()
