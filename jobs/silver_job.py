"""Entrypoint do job da camada Silver."""

from pipeline.common.glue import load_glue_env
from pipeline.transformations.silver import run

if __name__ == "__main__":
    load_glue_env()
    run()
