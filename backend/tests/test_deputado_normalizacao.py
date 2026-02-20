from backend.database import db_instance


def test_upsert_deputado_normalizado_persists_core_fields():
    deputado_id = 999001
    db_instance.upsert_deputado_normalizado(
        deputado_id,
        {
            "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/999001",
            "nome_civil": "DEPUTADO TESTE",
            "status_nome": "Deputado Teste",
            "status_sigla_partido": "ABC",
            "status_sigla_uf": "SP",
            "foto_url": "https://example.com/foto.jpg",
            "foto_content_type": "image/jpeg",
            "rede_social_json": "[]",
        },
    )
    rows = db_instance.list_deputados_normalizados(limit=500)
    found = next((row for row in rows if row["id"] == deputado_id), None)
    assert found is not None
    assert found["status_nome"] == "Deputado Teste"
    assert found["status_sigla_partido"] == "ABC"
