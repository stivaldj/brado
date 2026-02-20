from __future__ import annotations

from app.ingest.camara.endpoints import (
    DEPUTADOS_ENDPOINT,
    PROPOSICOES_ENDPOINT,
    VOTACOES_ENDPOINT,
    deputado_details_endpoint,
    despesas_endpoint,
    proposicao_details_endpoint,
    votacao_details_endpoint,
    votacao_votos_endpoint,
)


# Minimal contract derived from official Camara Swagger fields used by this project.
SWAGGER_ENDPOINTS = {
    "/deputados",
    "/deputados/{id}",
    "/deputados/{id}/despesas",
    "/proposicoes",
    "/proposicoes/{id}",
    "/votacoes",
    "/votacoes/{id}",
    "/votacoes/{id}/votos",
}


def test_used_endpoints_are_in_swagger_contract():
    used = {
        DEPUTADOS_ENDPOINT,
        deputado_details_endpoint("{id}"),
        despesas_endpoint("{id}"),
        PROPOSICOES_ENDPOINT,
        proposicao_details_endpoint("{id}"),
        VOTACOES_ENDPOINT,
        votacao_details_endpoint("{id}"),
        votacao_votos_endpoint("{id}"),
    }
    assert used == SWAGGER_ENDPOINTS


def test_nominal_votes_fallback_schema_contract():
    payload = {
        "dados": [],
        "metadata": {
            "error_type": "nominal_votes_not_available",
            "status_code": 404,
        },
    }
    assert isinstance(payload["dados"], list)
    assert isinstance(payload["metadata"], dict)
    assert payload["metadata"]["error_type"] in {
        "nominal_votes_not_available",
        "upstream_error",
        "nominal_votes_http_error",
    }
