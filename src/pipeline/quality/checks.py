"""Regras de qualidade de dados aplicadas sobre as camadas.

Cada checagem recebe um DataFrame (ou dois, no caso de integridade referencial) e
devolve um CheckResult com o veredito e o detalhe. As regras cobrem o que o
desafio pede: duplicidade, valores ausentes, validacao de chaves de
relacionamento e consistencia entre tabelas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame

CRITICAL = "critical"
WARNING = "warning"


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    severity: str
    details: str


def check_no_duplicates(
    df: DataFrame, keys: list[str], name: str, severity: str = CRITICAL
) -> CheckResult:
    duplicados = df.groupBy(*keys).count().filter("count > 1").count()
    return CheckResult(
        name=name,
        passed=duplicados == 0,
        severity=severity,
        details=f"{duplicados} chave(s) duplicada(s) em {keys}",
    )


def check_not_null(
    df: DataFrame, columns: list[str], name: str, severity: str = CRITICAL
) -> CheckResult:
    from pyspark.sql import functions as F

    condicao = None
    for coluna in columns:
        nulo = F.col(coluna).isNull()
        condicao = nulo if condicao is None else (condicao | nulo)
    ausentes = df.filter(condicao).count() if condicao is not None else 0
    return CheckResult(
        name=name,
        passed=ausentes == 0,
        severity=severity,
        details=f"{ausentes} linha(s) com valor ausente em {columns}",
    )


def check_referential_integrity(
    child: DataFrame,
    parent: DataFrame,
    child_keys: list[str],
    parent_keys: list[str],
    name: str,
    severity: str = CRITICAL,
) -> CheckResult:
    condicao = [child[ck] == parent[pk] for ck, pk in zip(child_keys, parent_keys, strict=True)]
    orfaos = child.join(parent, condicao, "left_anti").count()
    return CheckResult(
        name=name,
        passed=orfaos == 0,
        severity=severity,
        details=f"{orfaos} registro(s) sem correspondencia em {parent_keys}",
    )


def check_value_range(
    df: DataFrame,
    column: str,
    minimo: float,
    maximo: float,
    name: str,
    severity: str = CRITICAL,
) -> CheckResult:
    from pyspark.sql import functions as F

    fora = df.filter(
        F.col(column).isNotNull() & ((F.col(column) < minimo) | (F.col(column) > maximo))
    ).count()
    return CheckResult(
        name=name,
        passed=fora == 0,
        severity=severity,
        details=f"{fora} valor(es) de {column} fora do intervalo [{minimo}, {maximo}]",
    )


def check_consistency_leq(
    df: DataFrame, column_a: str, column_b: str, name: str, severity: str = CRITICAL
) -> CheckResult:
    """Garante que column_a nunca passa de column_b (ex: alfabetizados <= avaliados)."""
    from pyspark.sql import functions as F

    inconsistentes = df.filter(F.col(column_a) > F.col(column_b)).count()
    return CheckResult(
        name=name,
        passed=inconsistentes == 0,
        severity=severity,
        details=f"{inconsistentes} linha(s) com {column_a} maior que {column_b}",
    )
