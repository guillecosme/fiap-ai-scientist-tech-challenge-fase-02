"""Testes de integração das transformações Silver e Gold.

Escrevem um Bronze pequeno num data_root temporário, rodam as transformações de
verdade (Silver e Gold) e conferem a lógica que sustenta a camada analítica: a
integração de batch e streaming no mesmo grão e o cálculo de meta e gap na Gold.
"""

import pytest

from pipeline.common import layer_path, read_parquet, write_parquet


@pytest.fixture
def gold_pronta(spark, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    def bronze(name, rows, cols):
        write_parquet(spark.createDataFrame(rows, cols), layer_path("bronze", name), mode="overwrite")

    bronze("uf", [(35, "SP", "Sao Paulo", 3, "Sudeste"), (33, "RJ", "Rio de Janeiro", 3, "Sudeste")],
           ["id_uf", "sigla_uf", "nome_uf", "id_regiao", "nome_regiao"])
    bronze("municipio", [(3550308, "Sao Paulo", "SP", 35), (3304557, "Rio de Janeiro", "RJ", 33)],
           ["id_municipio", "nome_municipio", "sigla_uf", "id_uf"])
    bronze("meta_brasil", [(2024, 54.0), (2025, 60.0)], ["ano", "meta_indicador"])
    bronze("meta_uf", [(2024, "SP", 72.0), (2025, "SP", 74.0), (2024, "RJ", 70.0), (2025, "RJ", 72.0)],
           ["ano", "sigla_uf", "meta_indicador"])
    bronze("meta_municipio",
           [(2024, 3550308, 74.0), (2025, 3550308, 74.0), (2024, 3304557, 68.0), (2025, 3304557, 68.0)],
           ["ano", "id_municipio", "meta_indicador"])
    bronze("alunos",
           [(2024, 3550308, "publica", 1000, 800, 750.0),
            (2025, 3550308, "publica", 1000, 830, 755.0),
            (2024, 3304557, "publica", 500, 300, 720.0)],
           ["ano", "id_municipio", "rede", "qtd_avaliados", "qtd_alfabetizados", "media_proficiencia"])
    # evento de streaming para o mesmo grão de Sao Paulo em 2024
    eventos = spark.createDataFrame(
        [(2024, 3550308, "publica", 200, 180, 760.0)],
        ["ano", "id_municipio", "rede", "qtd_avaliados", "qtd_alfabetizados", "media_proficiencia"],
    )
    eventos.write.mode("overwrite").json(layer_path("bronze", "alunos_streaming"))

    from pipeline.transformations import gold, silver

    silver.run()
    gold.run()
    return spark


def _linha(df, **filtros):
    for col, val in filtros.items():
        df = df.filter(df[col] == val)
    linhas = df.collect()
    assert len(linhas) == 1, f"esperava 1 linha para {filtros}, veio {len(linhas)}"
    return linhas[0]


def test_silver_integra_batch_e_streaming(gold_pronta):
    spark = gold_pronta
    alunos = read_parquet(spark, layer_path("silver", "alunos"))
    sp = _linha(alunos, ano=2024, id_municipio=3550308, rede="publica")
    # batch (1000/800) somado ao streaming (200/180)
    assert sp["qtd_avaliados"] == 1200
    assert sp["qtd_alfabetizados"] == 980
    # indicador = 100 * 980 / 1200
    assert sp["indicador_pct"] == 81.7
    # proficiencia como media ponderada pelos avaliados: (750*1000 + 760*200) / 1200
    assert sp["media_proficiencia"] == 751.7
    # enriquecido com territorio
    assert sp["sigla_uf"] == "SP"
    assert sp["nome_regiao"] == "Sudeste"


def test_silver_grao_unico_por_ano_municipio_rede(gold_pronta):
    spark = gold_pronta
    alunos = read_parquet(spark, layer_path("silver", "alunos"))
    chaves = alunos.select("ano", "id_municipio", "rede")
    assert chaves.count() == chaves.distinct().count()


def test_gold_fato_calcula_meta_e_gap(gold_pronta):
    spark = gold_pronta
    fato = read_parquet(spark, layer_path("gold", "fato_alfabetizacao"))
    sp = _linha(fato, ano=2024, id_municipio=3550308, rede="publica")
    # indicador 81.7 contra meta 74.0
    assert sp["atingiu_meta"] is True
    assert sp["gap_meta_pp"] == 7.7
    rj = _linha(fato, ano=2024, id_municipio=3304557, rede="publica")
    # indicador 60.0 contra meta 68.0: nao atingiu, gap negativo
    assert rj["atingiu_meta"] is False
    assert rj["gap_meta_pp"] == -8.0


def test_gold_evolucao_temporal_variacao_ano_a_ano(gold_pronta):
    spark = gold_pronta
    evolucao = read_parquet(spark, layer_path("gold", "evolucao_temporal"))
    sp2025 = _linha(evolucao, ano=2025, id_municipio=3550308)
    # 2024 integra batch e streaming (980/1200 = 81.7) e 2025 fica em 83.0 (830/1000)
    assert sp2025["indicador_ano_anterior"] == 81.7
    assert sp2025["variacao_pp"] == 1.3
