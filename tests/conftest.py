import pytest


@pytest.fixture(scope="session")
def spark():
    """SparkSession local para os testes. Pula os testes se o Spark/Java nao
    estiver disponivel no ambiente, para nao quebrar a suite leve."""
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession

    try:
        session = (
            SparkSession.builder.master("local[1]")
            .appName("tests")
            .config("spark.ui.enabled", "false")
            .getOrCreate()
        )
    except Exception as exc:  # pragma: no cover - depende do ambiente
        pytest.skip(f"Spark indisponivel: {exc}")
    yield session
    session.stop()
