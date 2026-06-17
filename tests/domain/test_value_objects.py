"""Unit tests for shared value objects."""
from decimal import Decimal

import pytest

from garage_app.domain.shared.value_objects import Money, Immatriculation


class TestMoney:
    def test_addition(self):
        a = Money.of("100.00")
        b = Money.of("50.00")
        assert (a + b).amount == Decimal("150.00")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Money(Decimal("-1"))

    def test_format_fr_eur(self):
        m = Money.of("1234.56", "EUR")
        assert "€" in m.format("fr")

    def test_format_fr_tnd(self):
        m = Money.of("1234.567")   # default TND
        result = m.format("fr")
        assert "DT" in result
        assert "1 234" in result   # thousands separator

    def test_multiply(self):
        m = Money.of("10") * 3
        assert m.amount == Decimal("30")


class TestImmatriculation:
    def test_siv_format(self):
        i = Immatriculation("AB-123-CD")
        assert str(i) == "AB-123-CD"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            Immatriculation("INVALID")

    def test_normalizes_to_upper(self):
        i = Immatriculation("ab-123-cd")
        assert str(i) == "AB-123-CD"
