from pipeline.ingestion.streaming_producer import generate_events


def test_generate_events_respeita_a_quantidade():
    eventos = generate_events(count=10, ano=2025)
    assert len(eventos) == 10


def test_evento_tem_os_campos_esperados():
    evento = generate_events(count=1, ano=2025)[0]
    esperado = {
        "event_id",
        "event_time",
        "event_type",
        "ano",
        "id_municipio",
        "rede",
        "qtd_avaliados",
        "qtd_alfabetizados",
        "media_proficiencia",
    }
    assert esperado.issubset(evento.keys())


def test_alfabetizados_nunca_passa_de_avaliados():
    for evento in generate_events(count=200, ano=2025):
        assert evento["qtd_alfabetizados"] <= evento["qtd_avaliados"]


def test_geracao_e_deterministica_com_a_mesma_seed():
    a = generate_events(count=5, ano=2025, seed=7)
    b = generate_events(count=5, ano=2025, seed=7)
    assert [e["id_municipio"] for e in a] == [e["id_municipio"] for e in b]
