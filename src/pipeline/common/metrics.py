"""Emissao de metricas de observabilidade da pipeline.

Cada etapa publica metricas de latencia, volume processado e falhas no
CloudWatch. Em ambiente sem AWS (execucao local), as metricas sao apenas
impressas, para nao quebrar o fluxo nem exigir credenciais.
"""

from __future__ import annotations

import os
import time
from types import TracebackType

NAMESPACE = "Alfabetizacao/Pipeline"


def emit_metric(
    name: str,
    value: float,
    unit: str = "Count",
    dimensions: dict[str, str] | None = None,
) -> None:
    dimensions = dimensions or {}
    monitoring_on = os.getenv("MONITORING_ENABLED", "false").lower() == "true"
    if not monitoring_on:
        print(f"[metrica] {name}={value} {unit} {dimensions}")
        return
    try:
        import boto3

        client = boto3.client("cloudwatch", endpoint_url=os.getenv("AWS_ENDPOINT_URL"))
        client.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    "MetricName": name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": [{"Name": k, "Value": v} for k, v in dimensions.items()],
                }
            ],
        )
    except Exception as exc:  # pragma: no cover - depende do ambiente
        print(f"[metrica][falha ao publicar] {name}={value}: {exc}")


class StageMonitor:
    """Mede a duracao de uma etapa e publica sucesso, falha e latencia."""

    def __init__(self, stage: str) -> None:
        self.stage = stage
        self._start = 0.0

    def __enter__(self) -> StageMonitor:
        self._start = time.monotonic()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        duracao = time.monotonic() - self._start
        dims = {"stage": self.stage}
        emit_metric("StageDurationSeconds", round(duracao, 2), "Seconds", dims)
        if exc_type is None:
            emit_metric("StageSuccess", 1, "Count", dims)
        else:
            emit_metric("StageFailure", 1, "Count", dims)
