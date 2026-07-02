"""Entrypoint do job de ingestao batch.

Funciona tanto rodado localmente (python jobs/batch_ingest_job.py) quanto como
job do AWS Glue, que invoca este mesmo arquivo. Toda a logica vive em
pipeline.ingestion.batch_ingest para manter o entrypoint fino.
"""

from pipeline.ingestion.batch_ingest import main

if __name__ == "__main__":
    main()
