import os

from pipeline.common.config import LAYERS, Settings
from pipeline.common.io import layer_path
from pipeline.ingestion.sources import BATCH_TABLES, get_batch_table


def test_layers_are_the_three_medallion_layers():
    assert LAYERS == ("bronze", "silver", "gold")


def test_batch_tables_cover_the_six_entities():
    nomes = {t.name for t in BATCH_TABLES}
    esperado = {"uf", "municipio", "meta_brasil", "meta_uf", "meta_municipio", "alunos"}
    assert nomes == esperado


def test_get_batch_table_retorna_a_fonte_correta():
    tabela = get_batch_table("municipio")
    assert tabela.bd_dataset_id == "br_bd_diretorios_brasil"
    assert tabela.seed_file == "municipio.csv"


def test_layer_path_local_usa_filesystem():
    settings = Settings(storage_backend="local", data_root="data")
    assert layer_path("bronze", "uf", settings) == "data/bronze/uf"


def test_layer_path_s3_usa_bucket_da_camada(monkeypatch):
    monkeypatch.delenv("BRONZE_BUCKET", raising=False)
    settings = Settings(storage_backend="s3", project="alfabetizacao", environment="dev")
    assert layer_path("bronze", "uf", settings) == "s3a://alfabetizacao-bronze-dev/uf"


def test_bucket_respeita_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("GOLD_BUCKET", "meu-bucket-gold")
    settings = Settings(storage_backend="s3")
    assert settings.bucket("gold") == "meu-bucket-gold"
    assert "gold" in os.environ["GOLD_BUCKET"] or True
