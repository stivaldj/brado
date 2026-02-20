from __future__ import annotations

from typing import Any

from .canonical import (
    bill_id,
    expense_id,
    organization_id,
    parse_date,
    person_id,
    vote_action_id,
    vote_event_id,
)


def normalize_person(deputado: dict[str, Any]) -> dict[str, Any]:
    pid = person_id(deputado.get("id"))
    ultimo = deputado.get("ultimoStatus", {})
    return {
        "id": pid,
        "sourceId": deputado.get("id"),
        "name": deputado.get("nomeCivil") or deputado.get("nome") or ultimo.get("nome"),
        "electoralName": ultimo.get("nomeEleitoral"),
        "party": ultimo.get("siglaPartido"),
        "state": ultimo.get("siglaUf"),
        "photoUrl": ultimo.get("urlFoto"),
        "email": ultimo.get("email"),
        "lastSeenAt": deputado.get("uri") or ultimo.get("uri"),
    }


def normalize_bill(proposicao: dict[str, Any]) -> dict[str, Any]:
    bid = bill_id(proposicao.get("id"))
    return {
        "id": bid,
        "sourceId": proposicao.get("id"),
        "siglaTipo": proposicao.get("siglaTipo"),
        "numero": proposicao.get("numero"),
        "ano": proposicao.get("ano"),
        "ementa": proposicao.get("ementa"),
        "dataApresentacao": parse_date(proposicao.get("dataApresentacao")),
        "uri": proposicao.get("uri"),
    }


def normalize_vote_event(votacao: dict[str, Any]) -> dict[str, Any]:
    vid = vote_event_id(votacao.get("id"))
    return {
        "id": vid,
        "sourceId": votacao.get("id"),
        "uri": votacao.get("uri"),
        "dataHoraRegistro": votacao.get("dataHoraRegistro"),
        "aprovacao": votacao.get("aprovacao"),
        "descricao": votacao.get("descricao"),
        "billId": bill_id(votacao.get("idProposicao")) if votacao.get("idProposicao") else None,
    }


def normalize_vote_action(voto: dict[str, Any], vote_event_node_id: str, person_node_id: str) -> dict[str, Any]:
    return {
        "id": vote_action_id(vote_event_node_id, person_node_id),
        "voteEventId": vote_event_node_id,
        "personId": person_node_id,
        "position": voto.get("tipoVoto") or voto.get("voto"),
        "partyOrientation": voto.get("orientacaoBancada"),
    }


def normalize_expense(expense: dict[str, Any], deputado_id: Any) -> dict[str, Any]:
    row_id = expense.get("codDocumento") or f"{deputado_id}:{expense.get('ano')}:{expense.get('mes')}:{expense.get('valorDocumento')}:{expense.get('nomeFornecedor')}"
    return {
        "id": expense_id(row_id),
        "sourceId": row_id,
        "personId": person_id(deputado_id),
        "organizationId": organization_id(expense.get("cnpjCpfFornecedor") or expense.get("nomeFornecedor")),
        "value": expense.get("valorLiquido") or expense.get("valorDocumento"),
        "documentDate": parse_date(expense.get("dataDocumento")),
        "year": expense.get("ano"),
        "month": expense.get("mes"),
        "supplierName": expense.get("nomeFornecedor"),
        "expenseType": expense.get("tipoDespesa"),
    }
