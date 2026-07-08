from pipeline.quality.checks import (
    check_consistency_leq,
    check_no_duplicates,
    check_not_null,
    check_referential_integrity,
    check_value_range,
)


def test_duplicates_detecta_chave_repetida(spark):
    df = spark.createDataFrame([(1,), (1,), (2,)], ["id"])
    resultado = check_no_duplicates(df, ["id"], "t")
    assert resultado.passed is False


def test_duplicates_aprova_quando_unico(spark):
    df = spark.createDataFrame([(1,), (2,), (3,)], ["id"])
    assert check_no_duplicates(df, ["id"], "t").passed is True


def test_not_null_detecta_ausente(spark):
    df = spark.createDataFrame([(1, "a"), (2, None)], ["id", "nome"])
    assert check_not_null(df, ["nome"], "t").passed is False


def test_referential_integrity_detecta_orfao(spark):
    filho = spark.createDataFrame([(1,), (2,), (99,)], ["id_uf"])
    pai = spark.createDataFrame([(1,), (2,)], ["id_uf"])
    assert check_referential_integrity(filho, pai, ["id_uf"], ["id_uf"], "t").passed is False


def test_consistency_leq_detecta_violacao(spark):
    df = spark.createDataFrame([(10, 8)], ["alfabetizados", "avaliados"])
    assert check_consistency_leq(df, "alfabetizados", "avaliados", "t").passed is False


def test_value_range_detecta_fora_da_faixa(spark):
    df = spark.createDataFrame([(50.0,), (150.0,)], ["indicador_pct"])
    assert check_value_range(df, "indicador_pct", 0, 100, "t").passed is False
