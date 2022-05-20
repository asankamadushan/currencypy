"""
The unit tests for the CurrencyConvertor class.
"""
import time
from datetime import datetime

import pytest
from currencypy.currency_convertor import CurrencyConvertor
from currencypy.exceptions import CurrencyAPIException


@pytest.mark.parametrize(
    "from_currency, to_currency, amount, expected",
    [("USD", "LKR", 100, 18283.9983), ("USD", "USD", 100, 100)],
)
def test_convert_between_different_currencies(
    from_currency, to_currency, amount, expected
):
    """
    Test the convert method of the CurrencyConvertor class.
    """
    currency_convertor = CurrencyConvertor()
    assert (
        currency_convertor.convert(
            amount,
            from_currency=from_currency,
            to_currency=to_currency,
            date=datetime(2019, 1, 1),
        )
        == expected
    )


def test_get_currency_rates_with_invalid_from_currency():
    """
    Test the get_currency_rates method of the CurrencyConvertor class.
    """
    currency_convertor = CurrencyConvertor()
    time.sleep(1)
    with pytest.raises(CurrencyAPIException):
        currency_convertor.get_currency_rates("INR", "USD", datetime(2019, 1, 1))


@pytest.mark.parametrize(
    "from_currency, to_currency, expected",
    [("USD", "LKR", 182.839983)],
)
def test_get_currency_rates(from_currency, to_currency, expected):
    """
    Test the get_currency_rates method of the CurrencyConvertor class.
    """
    currency_convertor = CurrencyConvertor()
    time.sleep(2)
    assert (
        currency_convertor.get_currency_rates(
            from_currency, to_currency, datetime(2019, 1, 1)
        )
        == expected
    )
