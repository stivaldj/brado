from app.proof.hashing import sha256_json_canonical


def test_sha256_json_canonical_is_deterministic() -> None:
    left = {"b": 2, "a": 1, "nested": {"z": 9, "x": 8}}
    right = {"nested": {"x": 8, "z": 9}, "a": 1, "b": 2}
    assert sha256_json_canonical(left) == sha256_json_canonical(right)
