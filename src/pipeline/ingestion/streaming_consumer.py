"""Consumidor dos eventos de streaming, empacotado como funcao Lambda.

E acionado pelo Kinesis (event source mapping), decodifica os registros e grava
o lote bruto no Bronze, numa pasta de streaming particionada por data. Mantido
sem dependencia do restante do pacote e sem Spark, para empacotar leve no Lambda
(boto3 ja faz parte do runtime).

A Silver depois unifica esses eventos com a carga batch de alunos.
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import uuid

import boto3


def _decode_records(event: dict) -> list[dict]:
    registros = []
    for record in event.get("Records", []):
        payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
        registros.append(json.loads(payload))
    return registros


def handler(event: dict, context: object = None) -> dict:
    bucket = os.environ["BRONZE_BUCKET"]
    prefix = os.getenv("STREAMING_PREFIX", "alunos_streaming")
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")

    registros = _decode_records(event)
    if not registros:
        return {"received": 0, "written": 0}

    ingestion_date = dt.date.today().isoformat()
    body = "\n".join(json.dumps(r) for r in registros).encode("utf-8")
    key = f"{prefix}/ingestion_date={ingestion_date}/part-{uuid.uuid4().hex}.json"

    s3 = boto3.client("s3", endpoint_url=endpoint_url)
    s3.put_object(Bucket=bucket, Key=key, Body=body)

    return {"received": len(registros), "written": len(registros), "key": key}
