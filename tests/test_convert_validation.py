"""
Tests for CurrencyConvertor.convert validation (unsupported currencies).

These lock the public convert API; lower-level get_currency_rates tests alone
do not prove callers using Money and to_currency see the same errors.
"""

import re
from decimal import Decimal
from unittest.mock import patch

import pytest
from currencypy.currency_convertor import CurrencyConvertor
from currencypy.exceptions import CurrencyException
from currencypy.money import Money


def test_convert_raises_for_unsupported_money_currency():
    """Invalid source currency on Money is rejected; no HTTP request."""
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        currency_convertor = CurrencyConvertor()
        with pytest.raises(
            CurrencyException,
            match=re.escape("KKI is not a supported currency"),
        ):
            currency_convertor.convert(Money(Decimal("100"), "KKI"), to_currency="USD")
        mocker.assert_not_called()


def test_convert_raises_for_unsupported_to_currency():
    """Invalid to_currency is rejected; no HTTP request."""
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        currency_convertor = CurrencyConvertor()
        with pytest.raises(
            CurrencyException,
            match=re.escape("KKI is not a supported currency"),
        ):
            currency_convertor.convert(Money(Decimal("100"), "USD"), to_currency="KKI")
        mocker.assert_not_called()
