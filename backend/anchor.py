
"""Stub for anchoring Merkle roots.

In a production system this would interact with a permissioned blockchain and
periodically publish roots to a public chain.  Here we append entries to
a JSON log in the backend folder to simulate anchoring.
"""
import time
import json
from pathlib import Path

# Anchor log will live next to this module
ANCHOR_FILE = Path(__file__).parent / 'anchor_log.json'


def _load_log():
    if ANCHOR_FILE.exists():
        try:
            return json.loads(ANCHOR_FILE.read_text())
        except Exception:
            return []
    return []


def anchor_root(entry_type: str, root: str) -> dict:
    """Append a root hash to the anchor log with a timestamp.

    Args:
        entry_type: A string describing what the root represents (e.g.,
            'checkin:event_id' or 'vote:theme_id').
        root: The Merkle root as a hex string.

    Returns:
        The log entry that was appended.
    """
    log = _load_log()
    entry = {
        'key': entry_type,
        'type': entry_type,
        'root': root,
        'timestamp': int(time.time())
    }
    log.append(entry)
    ANCHOR_FILE.write_text(json.dumps(log, indent=2))
    return entry
