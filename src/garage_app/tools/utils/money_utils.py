from __future__ import annotations

from decimal import Decimal


def format_currency(amount: Decimal | float, locale: str = "fr") -> str:
    amount = Decimal(str(amount))
    if locale == "fr":
        formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
        return f"{formatted} €"
    return f"€{amount:,.2f}"
