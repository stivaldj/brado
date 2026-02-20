from app.normalize.mappers import normalize_bill, normalize_expense, normalize_person, normalize_vote_event


def test_normalize_person() -> None:
    node = normalize_person({"id": 1, "nomeCivil": "Nome", "ultimoStatus": {"siglaPartido": "PT", "siglaUf": "SP"}})
    assert node["id"] == "camara:person:1"
    assert node["party"] == "PT"


def test_normalize_bill() -> None:
    node = normalize_bill({"id": 2, "siglaTipo": "PL", "numero": 10, "ano": 2020})
    assert node["id"] == "camara:bill:2"


def test_normalize_vote_event() -> None:
    node = normalize_vote_event({"id": 3, "idProposicao": 2})
    assert node["id"] == "camara:vote_event:3"
    assert node["billId"] == "camara:bill:2"


def test_normalize_expense() -> None:
    node = normalize_expense({"codDocumento": "x1", "nomeFornecedor": "ACME", "valorDocumento": 10}, 99)
    assert node["id"] == "camara:expense:x1"
    assert node["personId"] == "camara:person:99"
