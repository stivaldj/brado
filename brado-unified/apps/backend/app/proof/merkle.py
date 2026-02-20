import hashlib
from typing import List, Dict, Any


def merkle_root(leaves: List[str]) -> str:
    """Compute the Merkle root of a list of hexadecimal leaf hashes.
    Each leaf should be a hex string (without 0x prefix). If the number of
    leaves is odd, the last hash is duplicated. Hashes are concatenated
    and hashed with SHA‑256 at each level until one root remains.
    """
    if not leaves:
        return ''
    layer = list(leaves)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        next_layer = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            new_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            next_layer.append(new_hash)
        layer = next_layer
    return layer[0]


def build_merkle(leaves: List[str]) -> Dict[str, Any]:
    """Build a Merkle tree representation.

    Returns a dictionary with the following keys:
    - ``root``: the Merkle root hash (hex string)
    - ``leaf_count``: total number of leaves provided
    - ``algorithm``: fixed string ``"sha256"``
    - ``duplicated_last_if_odd``: ``True`` (the implementation duplicates the last
      leaf when the number of leaves is odd)
    """
    root = merkle_root(leaves)
    return {
        "root": root,
        "leaf_count": len(leaves),
        "algorithm": "sha256",
        "duplicated_last_if_odd": True,
    }
