"""Ponte entre os argumentos do AWS Glue e a configuracao por variavel de ambiente.

Os jobs leem configuracao de variaveis de ambiente. Quando rodam no Glue, os
parametros chegam como argumentos do job, nao como env. Esta funcao detecta o
ambiente Glue, le os parametros conhecidos e os exporta como variaveis de
ambiente antes de a pipeline iniciar. Fora do Glue (local), e um no-op.
"""

from __future__ import annotations

import os
import sys

_GLUE_PARAMS = [
    "STORAGE_BACKEND",
    "BRONZE_BUCKET",
    "SILVER_BUCKET",
    "GOLD_BUCKET",
    "AWS_REGION",
    "BD_BILLING_PROJECT_ID",
]


def load_glue_env() -> None:
    try:
        from awsglue.utils import getResolvedOptions
    except ImportError:
        return

    presentes = [p for p in _GLUE_PARAMS if f"--{p}" in sys.argv]
    if not presentes:
        return
    opcoes = getResolvedOptions(sys.argv, presentes)
    for chave, valor in opcoes.items():
        os.environ[chave] = valor
