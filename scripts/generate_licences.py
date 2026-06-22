"""
Generate 100 unique licence keys for Gestion Réparation Voiture v1.0.0.
Output: licences/licence_keys.txt

Usage:
  python scripts/generate_licences.py
  python scripts/generate_licences.py --count 200 --out licences/extra.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from garage_app.domain.societe.licence import generate_key, validate_key


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate licence keys")
    parser.add_argument("--count", type=int, default=100, help="Number of keys (default 100)")
    parser.add_argument("--out", default="licences/licence_keys.txt", help="Output file")
    args = parser.parse_args()

    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    keys: set[str] = set()
    while len(keys) < args.count:
        k = generate_key()
        if validate_key(k):   # sanity-check each generated key
            keys.add(k)

    sorted_keys = sorted(keys)

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Gestion Reparation Voiture v1.0.0 - Licence Keys\n")
        f.write("# Alfa Computers Apps — Ferid HELALI\n")
        f.write("# Contact: helaliferid@gmail.com | +216 22 45 79 16\n")
        f.write(f"# Generated: {args.count} keys\n")
        f.write("#\n")
        for key in sorted_keys:
            f.write(key + "\n")

    print(f"Generated {len(sorted_keys)} keys -> {out_path}")


if __name__ == "__main__":
    main()
