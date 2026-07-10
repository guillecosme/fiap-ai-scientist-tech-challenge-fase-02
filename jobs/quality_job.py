"""Entrypoint do gate de qualidade.

Roda apos a Silver e a Gold; se uma checagem critica falhar, sai com erro e
interrompe a orquestracao.
"""

from pipeline.common.glue import load_glue_env
from pipeline.common.metrics import StageMonitor
from pipeline.quality.runner import run

if __name__ == "__main__":
    load_glue_env()
    with StageMonitor("qualidade"):
        run()
