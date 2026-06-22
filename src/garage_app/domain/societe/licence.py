"""
Licence key domain logic — format: ALFA-XXXX-XXXX-XXXX-CHCK

Algorithm (offline, no server required):
  - G1/G2/G3: 4 random uppercase alphanumeric chars each
  - CHCK: last 4 hex chars of CRC32(G1+G2+G3)  →  tamper-evident checksum
  - Prefix "ALFA" ties keys to this product

Pure stdlib — no external imports.
"""
from __future__ import annotations

import random
import string
import zlib


_CHARSET = string.ascii_uppercase + string.digits
_PREFIX  = "ALFA"


def _checksum(g1: str, g2: str, g3: str) -> str:
    crc = zlib.crc32(f"{g1}{g2}{g3}".encode("ascii")) & 0xFFFFFFFF
    return format(crc, "08X")[-4:]


def generate_key() -> str:
    """Return a new random valid licence key."""
    g1 = "".join(random.choices(_CHARSET, k=4))
    g2 = "".join(random.choices(_CHARSET, k=4))
    g3 = "".join(random.choices(_CHARSET, k=4))
    return f"{_PREFIX}-{g1}-{g2}-{g3}-{_checksum(g1, g2, g3)}"


def validate_key(key: str) -> bool:
    """Return True iff the key has a valid ALFA-XXXX-XXXX-XXXX-CHCK structure and checksum."""
    parts = key.upper().strip().replace(" ", "").split("-")
    if len(parts) != 5:
        return False
    prefix, g1, g2, g3, check = parts
    if prefix != _PREFIX:
        return False
    if not all(len(p) == 4 for p in (g1, g2, g3, check)):
        return False
    valid_chars = set(_CHARSET)
    if not all(c in valid_chars for p in (g1, g2, g3, check) for c in p):
        return False
    return check == _checksum(g1, g2, g3)
