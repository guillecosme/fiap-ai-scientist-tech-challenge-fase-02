"""Ingestao batch das fontes para a camada Bronze.

Le cada tabela de referencia/meta (da Base dos Dados ou das amostras locais),
acrescenta metadados de ingestao e grava em Parquet no Bronze, particionado por
data de ingestao. O Bronze preserva o dado praticamente como veio da fonte.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from typing import TYPE_CHECKING

from pipeline.common import get_settings, get_spark, layer_path, write_parquet
from pipeline.common.metrics import emit_metric
from pipeline.ingestion.sources import BATCH_TABLES, SourceTable, get_batch_table

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


def _read_from_base_dos_dados(table: SourceTable, billing_project_id: str) -> DataFrame:
    import basedosdados as bd

    pdf = bd.read_table(
        dataset_id=table.bd_dataset_id,
        table_id=table.bd_table_id,
        billing_project_id=billing_project_id,
    )
    spark = get_spark("batch-ingest")
    return spark.createDataFrame(pdf)


def _read_from_seed(spark: SparkSession, table: SourceTable, seeds_dir: str) -> DataFrame:
    path = os.path.join(seeds_dir, table.seed_file)
    return spark.read.option("header", "true").option("inferSchema", "true").csv(path)


def load_source(spark: SparkSession, table: SourceTable, seeds_dir: str) -> DataFrame:
    settings = get_settings()
    if settings.billing_project_id:
        return _read_from_base_dos_dados(table, settings.billing_project_id)
    return _read_from_seed(spark, table, seeds_dir)


def ingest_table(
    spark: SparkSession,
    table: SourceTable,
    ingestion_date: str,
    seeds_dir: str,
) -> str:
    from pyspark.sql import functions as F

    df = load_source(spark, table, seeds_dir)
    enriched = (
        df.withColumn("ingestion_date", F.lit(ingestion_date))
        .withColumn("ingested_at", F.current_timestamp())
        .withColumn("source_table", F.lit(table.name))
    )
    destination = layer_path("bronze", table.name)
    write_parquet(enriched, destination, mode="overwrite", partition_by=["ingestion_date"])
    emit_metric("RecordsIngested", enriched.count(), "Count", {"table": table.name})
    return destination


def run(tables: list[str] | None, ingestion_date: str, seeds_dir: str) -> None:
    spark = get_spark("batch-ingest")
    selected = [get_batch_table(name) for name in tables] if tables else list(BATCH_TABLES)
    for table in selected:
        destination = ingest_table(spark, table, ingestion_date, seeds_dir)
        print(f"[bronze] {table.name} ingerido em {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestao batch para o Bronze")
    parser.add_argument("--table", action="append", help="Nome da tabela (pode repetir)")
    parser.add_argument(
        "--ingestion-date",
        default=dt.date.today().isoformat(),
        help="Data de ingestao usada como particao (YYYY-MM-DD)",
    )
    parser.add_argument("--seeds-dir", default="data/seeds", help="Diretorio das amostras locais")
    # parse_known_args ignora os argumentos extras que o Glue injeta no job.
    args, _ = parser.parse_known_args()
    run(args.table, args.ingestion_date, args.seeds_dir)


if __name__ == "__main__":
    main()
