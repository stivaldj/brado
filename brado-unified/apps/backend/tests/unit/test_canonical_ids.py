from app.normalize.canonical import (
    bill_id,
    expense_id,
    organization_id,
    person_id,
    vote_action_id,
    vote_event_id,
)


def test_canonical_ids_are_deterministic() -> None:
    assert person_id(123) == "camara:person:123"
    assert bill_id(987) == "camara:bill:987"
    assert vote_event_id("42") == "camara:vote_event:42"
    assert vote_action_id("camara:vote_event:42", "camara:person:123") == "camara:vote_action:camara:vote_event:42:camara:person:123"
    assert expense_id("abc") == "camara:expense:abc"
    assert organization_id("Fornecedor X") == "camara:org:FORNECEDOR X"
