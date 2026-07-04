"""Produtor de eventos simulados de alfabetizacao em tempo quase real.

Gera novas medicoes de desempenho (como se chegassem de avaliacoes recentes) e
as publica em um dos dois destinos:

- kinesis: envia para um Kinesis Data Stream (funciona contra a AWS real ou o
  LocalStack). E o caminho que exercita a arquitetura de streaming completa,
  com o consumidor Lambda gravando no Bronze.
- file: grava os eventos direto numa pasta de streaming do Bronze, em JSON por
  linha. E o caminho offline, util para rodar a pipeline localmente sem Kinesis.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import uuid

# Municipios usados nos eventos, alinhados com as amostras das fontes batch.
_MUNICIPIOS = [
    3550308,
    3509502,
    3304557,
    2927408,
    2918407,
    2304400,
    5300108,
    4314902,
    1501402,
]
_REDES = ["publica", "privada"]


def generate_events(count: int, ano: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    events = []
    for _ in range(count):
        id_municipio = rng.choice(_MUNICIPIOS)
        rede = rng.choice(_REDES)
        avaliados = rng.randint(80, 600)
        taxa = rng.uniform(0.45, 0.92) if rede == "publica" else rng.uniform(0.7, 0.97)
        alfabetizados = int(avaliados * taxa)
        proficiencia = round(rng.uniform(720, 800), 1)
        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "event_time": dt.datetime.now(dt.UTC).isoformat(),
                "event_type": "medicao",
                "ano": ano,
                "id_municipio": id_municipio,
                "rede": rede,
                "qtd_avaliados": avaliados,
                "qtd_alfabetizados": alfabetizados,
                "media_proficiencia": proficiencia,
            }
        )
    return events


def send_to_kinesis(events: list[dict], stream_name: str, endpoint_url: str | None) -> None:
    import boto3

    client = boto3.client("kinesis", endpoint_url=endpoint_url)
    for event in events:
        client.put_record(
            StreamName=stream_name,
            Data=json.dumps(event).encode("utf-8"),
            PartitionKey=str(event["id_municipio"]),
        )


def write_to_file(events: list[dict], output_dir: str, ingestion_date: str) -> str:
    target_dir = os.path.join(output_dir, f"ingestion_date={ingestion_date}")
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, f"events-{uuid.uuid4().hex}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Produtor de eventos de alfabetizacao")
    parser.add_argument("--count", type=int, default=50, help="Quantidade de eventos")
    parser.add_argument("--ano", type=int, default=2025, help="Ano de referencia dos eventos")
    parser.add_argument("--target", choices=["kinesis", "file"], default="kinesis")
    parser.add_argument("--stream", default="alfabetizacao-eventos-dev", help="Nome do stream")
    parser.add_argument(
        "--endpoint-url",
        default=os.getenv("AWS_ENDPOINT_URL"),
        help="Endpoint do Kinesis (use http://localhost:4566 com LocalStack)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/bronze/alunos_streaming",
        help="Pasta de saida quando target=file",
    )
    args = parser.parse_args()

    events = generate_events(args.count, args.ano)
    if args.target == "kinesis":
        send_to_kinesis(events, args.stream, args.endpoint_url)
        print(f"[streaming] {len(events)} eventos enviados ao stream {args.stream}")
    else:
        ingestion_date = dt.date.today().isoformat()
        path = write_to_file(events, args.output_dir, ingestion_date)
        print(f"[streaming] {len(events)} eventos gravados em {path}")


if __name__ == "__main__":
    main()
