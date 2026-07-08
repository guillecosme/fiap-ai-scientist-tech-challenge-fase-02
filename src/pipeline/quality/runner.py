"""Suite de qualidade e gate de promocao entre camadas.

Monta o conjunto de checagens sobre a Silver e a Gold, executa todas e aplica um
gate: se qualquer checagem critica falhar, levanta erro e interrompe a pipeline,
evitando que dado ruim suba de camada. Funciona como um quality gate de CI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pipeline.common import get_spark, layer_path, read_parquet
from pipeline.quality.checks import (
    CRITICAL,
    CheckResult,
    check_consistency_leq,
    check_no_duplicates,
    check_not_null,
    check_referential_integrity,
    check_value_range,
)

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class QualityGateError(RuntimeError):
    """Levantada quando uma ou mais checagens criticas falham."""


def build_suite(spark: SparkSession) -> list[CheckResult]:
    uf = read_parquet(spark, layer_path("silver", "uf"))
    municipio = read_parquet(spark, layer_path("silver", "municipio"))
    meta_municipio = read_parquet(spark, layer_path("silver", "meta_municipio"))
    alunos = read_parquet(spark, layer_path("silver", "alunos"))
    indicador = read_parquet(spark, layer_path("gold", "indicador_municipio"))

    return [
        # Municipio: chave unica, sem nulos e com UF existente.
        check_no_duplicates(municipio, ["id_municipio"], "municipio.chave_unica"),
        check_not_null(municipio, ["id_municipio", "sigla_uf"], "municipio.sem_nulos"),
        check_referential_integrity(municipio, uf, ["id_uf"], ["id_uf"], "municipio.fk_uf"),
        # Alunos integrado: grao unico, campos preenchidos, faixa e consistencia.
        check_no_duplicates(alunos, ["ano", "id_municipio", "rede"], "alunos.grao_unico"),
        check_not_null(
            alunos, ["ano", "id_municipio", "rede", "indicador_pct"], "alunos.sem_nulos"
        ),
        check_value_range(alunos, "indicador_pct", 0, 100, "alunos.indicador_0_100"),
        check_consistency_leq(
            alunos, "qtd_alfabetizados", "qtd_avaliados", "alunos.alfabetizados_leq_avaliados"
        ),
        check_referential_integrity(
            alunos, municipio, ["id_municipio"], ["id_municipio"], "alunos.fk_municipio"
        ),
        # Metas: grao unico e municipio existente.
        check_no_duplicates(meta_municipio, ["ano", "id_municipio"], "meta_municipio.grao_unico"),
        check_referential_integrity(
            meta_municipio,
            municipio,
            ["id_municipio"],
            ["id_municipio"],
            "meta_municipio.fk_municipio",
        ),
        # Gold: indicador dentro da faixa valida.
        check_value_range(indicador, "indicador_pct", 0, 100, "gold.indicador_0_100"),
    ]


def run_gate(results: list[CheckResult]) -> None:
    falhas_criticas = [r for r in results if not r.passed and r.severity == CRITICAL]
    for r in results:
        status = "OK" if r.passed else "FALHOU"
        print(f"[qualidade][{status}] {r.name}: {r.details}")
    if falhas_criticas:
        nomes = ", ".join(r.name for r in falhas_criticas)
        raise QualityGateError(f"Gate de qualidade reprovado em: {nomes}")
    print(f"[qualidade] gate aprovado, {len(results)} checagens executadas")


def run() -> None:
    spark = get_spark("quality")
    resultados = build_suite(spark)
    run_gate(resultados)


if __name__ == "__main__":
    run()
