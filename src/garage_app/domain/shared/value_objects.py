from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ValueObject:
    pass


# Supported currencies and their symbols
CURRENCY_SYMBOLS: dict[str, str] = {
    "TND": "DT",
    "EUR": "€",
    "USD": "$",
    "CAD": "CA$",
}


@dataclass(frozen=True)
class Money(ValueObject):
    amount: Decimal
    currency: str = "TND"   # Default: Tunisian Dinar

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError("Montant ne peut pas être négatif.")

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Devises incompatibles: {self.currency} vs {other.currency}.")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: int | Decimal) -> Money:
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def format(self, locale: str = "fr") -> str:
        symbol = CURRENCY_SYMBOLS.get(self.currency, self.currency)
        if locale == "fr":
            # French number format: 1 234,567 DT
            formatted = f"{self.amount:,.3f}".replace(",", " ").replace(".", ",")
            return f"{formatted} {symbol}"
        # English format: DT 1,234.567
        return f"{symbol} {self.amount:,.3f}"

    @classmethod
    def zero(cls, currency: str = "TND") -> Money:
        return cls(Decimal("0"), currency)

    @classmethod
    def of(cls, amount: float | str | Decimal, currency: str = "TND") -> Money:
        return cls(Decimal(str(amount)), currency)


@dataclass(frozen=True)
class Immatriculation(ValueObject):
    value: str

    def __post_init__(self) -> None:
        clean = self.value.upper().strip()
        # SIV format: AB-123-CD  or old format: 123 AB 75
        if not re.match(r'^[A-Z]{2}-\d{3}-[A-Z]{2}$', clean) and \
           not re.match(r'^\d{1,4}\s?[A-Z]{1,3}\s?\d{2,3}$', clean):
            raise ValueError(f"Immatriculation invalide: {self.value!r}")
        object.__setattr__(self, 'value', clean)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Vin(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if len(self.value) != 17:
            raise ValueError(f"VIN invalide: doit contenir 17 caractères.")
        object.__setattr__(self, 'value', self.value.upper())
