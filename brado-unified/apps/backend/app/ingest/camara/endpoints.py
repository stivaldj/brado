DEPUTADOS_ENDPOINT = "/deputados"
PROPOSICOES_ENDPOINT = "/proposicoes"
VOTACOES_ENDPOINT = "/votacoes"


def deputado_details_endpoint(deputado_id: int | str) -> str:
    return f"/deputados/{deputado_id}"


def votacao_details_endpoint(votacao_id: int | str) -> str:
    return f"/votacoes/{votacao_id}"


def votacao_votos_endpoint(votacao_id: int | str) -> str:
    return f"/votacoes/{votacao_id}/votos"


def proposicao_details_endpoint(proposicao_id: int | str) -> str:
    return f"/proposicoes/{proposicao_id}"


def despesas_endpoint(deputado_id: int | str) -> str:
    return f"/deputados/{deputado_id}/despesas"
