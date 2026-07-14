"""Configuracao central da pipeline, dirigida por variaveis de ambiente.

A mesma base de codigo roda em dois cenarios:

- local: as camadas vivem em diretorios Parquet sob ``data/`` e nenhuma
  credencial de nuvem e necessaria. E o caminho usado em dev e pelo avaliador.
- s3: as camadas vivem em buckets S3 (provisionados pelo Terraform), e os nomes
  dos buckets chegam por variavel de ambiente, ja que recebem um sufixo
  aleatorio para serem agnosticos a conta.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

SEED = 42

LAYERS = ("bronze", "silver", "gold")


@dataclass(frozen=True)
class Settings:
    project: str = field(default_factory=lambda: os.getenv("PROJECT", "alfabetizacao"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "dev"))
    region: str = field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))

    # "local" (filesystem) ou "s3"
    storage_backend: str = field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))
    data_root: str = field(default_factory=lambda: os.getenv("DATA_ROOT", "data"))

    # Endpoint da AWS. Vazio em conta real (usa o endpoint padrao de cada servico);
    # apontado para o LocalStack quando se quer o caminho de nuvem localmente.
    # E o unico interruptor entre "AWS real" e "LocalStack" no lado do codigo.
    aws_endpoint_url: str | None = field(default_factory=lambda: os.getenv("AWS_ENDPOINT_URL"))

    # Projeto de billing do Google Cloud, exigido pelo pacote basedosdados para
    # consultar o datalake (a cota de 1 TB/mes e gratuita). Opcional: sem ele, a
    # ingestao usa as amostras versionadas em data/seeds.
    billing_project_id: str | None = field(
        default_factory=lambda: os.getenv("BD_BILLING_PROJECT_ID")
    )

    def bucket(self, layer: str) -> str:
        """Nome do bucket de uma camada quando o backend e S3."""
        env_name = f"{layer.upper()}_BUCKET"
        return os.getenv(env_name, f"{self.project}-{layer}-{self.environment}")


def get_settings() -> Settings:
    return Settings()
