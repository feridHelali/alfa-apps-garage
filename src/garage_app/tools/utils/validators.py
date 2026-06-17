from __future__ import annotations

import re


def validate_siret(value: str) -> bool:
    return bool(re.match(r'^\d{14}$', value.replace(" ", "")))


def validate_immatriculation(value: str) -> bool:
    clean = value.upper().strip()
    return bool(
        re.match(r'^[A-Z]{2}-\d{3}-[A-Z]{2}$', clean) or
        re.match(r'^\d{1,4}\s?[A-Z]{1,3}\s?\d{2,3}$', clean)
    )


def validate_vin(value: str) -> bool:
    return len(value.strip()) == 17


def validate_email(value: str) -> bool:
    return bool(re.match(r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$', value.strip()))
