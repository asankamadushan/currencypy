"""
The unit tests for the CurrencyConvertor class.
"""
from datetime import datetime

import pytest
from requests_mock import Mocker
from currencypy.currency_convertor import CurrencyConvertor
from currencypy.exceptions import CurrencyException


@pytest.mark.parametrize(
    "from_currency, to_currency, amount, rate, expected",
    [
        ("USD", "LKR", 100, 182.839983, 18283.9983),
        ("USD", "USD", 100, 1, 100),
        ("USD", "INR", 100, 1.3598, 135.98),
    ],
)
def test_convert_between_different_currencies(
    from_currency, to_currency, amount, rate, expected
):
    """
    Test the convert method of the CurrencyConvertor class.
    """
    with Mocker() as mocker:
        mocker.get(
            "http://api.currencylayer.com/historical",
            json={
                "success": True,
                "terms": "https://currencylayer.com/terms",
                "privacy": "https://currencylayer.com/privacy",
                "quotes": {
                    f"{from_currency}{to_currency}": rate,
                },
            },
        )
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


@pytest.mark.parametrize(
    "from_currency, to_currency, date",
    [("USD", "KKI", datetime(2019, 1, 1)), ("USD", "IIi099", datetime(2019, 1, 1))],
)
def test_get_currency_rates_with_invalid_from_currency(
    from_currency, to_currency, date
):
    """
    Test the get_currency_rates method of the CurrencyConvertor class.
    """
    with Mocker() as mocker:
        mocker.get(
            "http://api.currencylayer.com/historical",
            json={
                "success": False,
                "error": {"code": 104, "info": "Invalid currency: INVALID"},
            },
        )
        currency_convertor = CurrencyConvertor()
        with pytest.raises(CurrencyException):
            currency_convertor.get_currency_rates(from_currency, to_currency, date)


@pytest.mark.parametrize(
    "from_currency, to_currency, expected",
    [("USD", "LKR", 182.839983)],
)
def test_get_currency_rates(from_currency: str, to_currency: str, expected: float):
    """
    Test the get_currency_rates method of the CurrencyConvertor class.
    """
    with Mocker() as mocker:
        mocker.get(
            "http://api.currencylayer.com/historical",
            json={
                "success": True,
                "terms": "https://currencylayer.com/terms",
                "privacy": "https://currencylayer.com/privacy",
                "quotes": {
                    "USDLKR": 182.839983,
                },
            },
        )
        currency_convertor = CurrencyConvertor()
        assert (
            currency_convertor.get_currency_rates(
                from_currency, to_currency, datetime(2019, 1, 1)
            )
            == expected
        )


def test_get_supported_currencies():
    """
    Test the get_supported_currencies method of the CurrencyConvertor class.
    """
    currency_convertor = CurrencyConvertor()
    assert list(currency_convertor.get_supported_currencies().keys()) == [
        "AED",
        "AFN",
        "ALL",
        "AMD",
        "ANG",
        "AOA",
        "ARS",
        "AUD",
        "AWG",
        "AZN",
        "BAM",
        "BBD",
        "BDT",
        "BGN",
        "BHD",
        "BIF",
        "BMD",
        "BND",
        "BOB",
        "BRL",
        "BSD",
        "BTC",
        "BTN",
        "BWP",
        "BYN",
        "BYR",
        "BZD",
        "CAD",
        "CDF",
        "CHF",
        "CLF",
        "CLP",
        "CNY",
        "COP",
        "CRC",
        "CUC",
        "CUP",
        "CVE",
        "CZK",
        "DJF",
        "DKK",
        "DOP",
        "DZD",
        "EGP",
        "ERN",
        "ETB",
        "EUR",
        "FJD",
        "FKP",
        "GBP",
        "GEL",
        "GGP",
        "GHS",
        "GIP",
        "GMD",
        "GNF",
        "GTQ",
        "GYD",
        "HKD",
        "HNL",
        "HRK",
        "HTG",
        "HUF",
        "IDR",
        "ILS",
        "IMP",
        "INR",
        "IQD",
        "IRR",
        "ISK",
        "JEP",
        "JMD",
        "JOD",
        "JPY",
        "KES",
        "KGS",
        "KHR",
        "KMF",
        "KPW",
        "KRW",
        "KWD",
        "KYD",
        "KZT",
        "LAK",
        "LBP",
        "LKR",
        "LRD",
        "LSL",
        "LTL",
        "LVL",
        "LYD",
        "MAD",
        "MDL",
        "MGA",
        "MKD",
        "MMK",
        "MNT",
        "MOP",
        "MRO",
        "MUR",
        "MVR",
        "MWK",
        "MXN",
        "MYR",
        "MZN",
        "NAD",
        "NGN",
        "NIO",
        "NOK",
        "NPR",
        "NZD",
        "OMR",
        "PAB",
        "PEN",
        "PGK",
        "PHP",
        "PKR",
        "PLN",
        "PYG",
        "QAR",
        "RON",
        "RSD",
        "RUB",
        "RWF",
        "SAR",
        "SBD",
        "SCR",
        "SDG",
        "SEK",
        "SGD",
        "SHP",
        "SLL",
        "SOS",
        "SRD",
        "STD",
        "SVC",
        "SYP",
        "SZL",
        "THB",
        "TJS",
        "TMT",
        "TND",
        "TOP",
        "TRY",
        "TTD",
        "TWD",
        "TZS",
        "UAH",
        "UGX",
        "USD",
        "UYU",
        "UZS",
        "VEF",
        "VND",
        "VUV",
        "WST",
        "XAF",
        "XAG",
        "XAU",
        "XCD",
        "XDR",
        "XOF",
        "XPF",
        "YER",
        "ZAR",
        "ZMK",
        "ZMW",
        "ZWL",
    ]
