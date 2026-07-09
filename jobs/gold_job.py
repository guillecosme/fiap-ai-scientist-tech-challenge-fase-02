"""Entrypoint do job da camada Gold."""

from pipeline.common.glue import load_glue_env
from pipeline.transformations.gold import run

if __name__ == "__main__":
    load_glue_env()
    run()
