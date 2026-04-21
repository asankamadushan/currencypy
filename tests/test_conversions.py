"""
The unit tests for the CurrencyConvertor class.
"""

import json
import logging
import re
import urllib.error
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from currencypy.currency_convertor import APIResponse, CurrencyConvertor
from currencypy.exceptions import CurrencyAPIException, CurrencyException
from currencypy.money import Money


@pytest.mark.parametrize(
    "from_currency, to_currency, amount, rate, expected_amount",
    [
        ("USD", "LKR", 100, 182.839983, "18283.9983"),
        ("USD", "INR", 100, 1.3598, "135.98"),
    ],
)
def test_convert_between_different_currencies(
    from_currency, to_currency, amount, rate, expected_amount
):
    """
    Cross-currency conversion uses the mocked API response.
    """
    data = {
        "success": True,
        "terms": "https://currencylayer.com/terms",
        "privacy": "https://currencylayer.com/privacy",
        "quotes": {
            f"{from_currency}{to_currency}": rate,
        },
    }
    mocked_response = APIResponse(200, True, data, {})

    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        mocker.return_value = mocked_response
        currency_convertor = CurrencyConvertor()
        result = currency_convertor.convert(
            Money(Decimal(str(amount)), from_currency),
            to_currency=to_currency,
        )
        assert result == Money(Decimal(expected_amount), to_currency)


def test_convert_same_currency_returns_amount_without_api_call():
    """
    Same from/to returns the amount immediately; get_currency_rates is never invoked.
    """
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        currency_convertor = CurrencyConvertor()
        result = currency_convertor.convert(
            Money(Decimal("100"), "USD"),
            to_currency="USD",
        )
        assert result == Money(Decimal("100"), "USD")
        mocker.assert_not_called()


def test_convert_result_currency_matches_to_currency():
    """Converted Money carries the target ISO currency code."""
    data = {
        "success": True,
        "terms": "https://currencylayer.com/terms",
        "privacy": "https://currencylayer.com/privacy",
        "quotes": {"USDJPY": 150.25},
    }
    mocked_response = APIResponse(200, True, data, {})
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        mocker.return_value = mocked_response
        currency_convertor = CurrencyConvertor()
        out = currency_convertor.convert(
            Money(Decimal("2"), "USD"),
            to_currency="JPY",
        )
        assert out.currency == "JPY"


def test_convert_uses_decimal_rates_not_float_drift():
    """
    Rate is parsed via Decimal(str(quote)); product matches exact Decimal math.
    """
    data = {
        "success": True,
        "terms": "https://currencylayer.com/terms",
        "privacy": "https://currencylayer.com/privacy",
        "quotes": {"USDEUR": 0.1},
    }
    mocked_response = APIResponse(200, True, data, {})
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        mocker.return_value = mocked_response
        currency_convertor = CurrencyConvertor()
        out = currency_convertor.convert(
            Money(Decimal("3"), "USD"),
            to_currency="EUR",
        )
        assert out.amount == Decimal("3") * Decimal("0.1")


def test_convert_with_historical_date_uses_historical_endpoint_and_money():
    """
    convert(..., date=...) resolves rates via the historical API and returns the
    same Money as the module doctest (end-to-end through convert, not only
    get_currency_rates).
    """
    data = {
        "success": True,
        "terms": "https://currencylayer.com/terms",
        "privacy": "https://currencylayer.com/privacy",
        "quotes": {
            "USDLKR": 182.839983,
        },
    }
    mocked_response = APIResponse(200, True, data, {})
    historical_date = datetime(2019, 1, 1)
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        mocker.return_value = mocked_response
        currency_convertor = CurrencyConvertor()
        result = currency_convertor.convert(
            Money(Decimal("100"), "USD"),
            to_currency="LKR",
            date=historical_date,
        )
        assert result == Money(Decimal("18283.9983"), "LKR")
        mocker.assert_called_once()
        path, kwargs = mocker.call_args[0][0], mocker.call_args[1]
        assert path == "historical"
        assert kwargs["params"]["date"] == "2019-01-01"


@pytest.mark.parametrize(
    "from_currency, to_currency, date, expected_msg",
    [
        (
            "USD",
            "KKI",
            datetime(2019, 1, 1),
            "KKI is not a supported currency",
        ),
        (
            "USD",
            "IIi099",
            datetime(2019, 1, 1),
            "IIi099 is not a supported currency",
        ),
        (
            "KKI",
            "USD",
            datetime(2019, 1, 1),
            "KKI is not a supported currency",
        ),
    ],
)
def test_get_currency_rates_raises_for_unsupported_currency(
    from_currency, to_currency, date, expected_msg
):
    """
    Validation fails before any HTTP call; message identifies which code was rejected.
    """
    currency_convertor = CurrencyConvertor()
    with pytest.raises(CurrencyException, match=re.escape(expected_msg)):
        currency_convertor.get_currency_rates(from_currency, to_currency, date)


@pytest.mark.parametrize(
    "from_currency, to_currency, expected",
    [("USD", "LKR", Decimal("182.839983"))],
)
def test_get_currency_rates(from_currency: str, to_currency: str, expected: Decimal):
    """
    Test the get_currency_rates method of the CurrencyConvertor class.
    """
    data = {
        "success": True,
        "terms": "https://currencylayer.com/terms",
        "privacy": "https://currencylayer.com/privacy",
        "quotes": {
            "USDLKR": 182.839983,
        },
    }
    mocked_response = APIResponse(200, True, data, {})
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        mocker.return_value = mocked_response
        currency_convertor = CurrencyConvertor()
        assert (
            currency_convertor.get_currency_rates(
                from_currency, to_currency, datetime(2019, 1, 1)
            )
            == expected
        )


def test_get_currency_rates_caches_historical_rates():
    """Second identical historical lookup does not call the HTTP client again."""
    data = {
        "success": True,
        "terms": "https://currencylayer.com/terms",
        "privacy": "https://currencylayer.com/privacy",
        "quotes": {
            "USDLKR": 182.839983,
        },
    }
    mocked_response = APIResponse(200, True, data, {})
    fixed_date = datetime(2019, 1, 1)
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        mocker.return_value = mocked_response
        currency_convertor = CurrencyConvertor()
        currency_convertor.get_currency_rates("USD", "LKR", fixed_date)
        currency_convertor.get_currency_rates("USD", "LKR", fixed_date)
        assert mocker.call_count == 1


def test_get_supported_currencies():
    """
    With live_update=False, the bundled default map is returned (single source of truth).
    """
    currency_convertor = CurrencyConvertor()
    assert (
        currency_convertor.get_supported_currencies()
        == CurrencyConvertor._DEFAULT_CURRENCY_LIST
    )


def test_raise_api_error_logs_before_exception(caplog):
    """API failures emit an ERROR log before CurrencyAPIException."""
    caplog.set_level(logging.ERROR, logger="currencypy.currency_convertor")
    data = {
        "success": False,
        "error": {"code": 101},
    }
    mocked_response = APIResponse(200, True, data, {})
    with patch("currencypy.currency_convertor.APIRequestHandler.get") as mocker:
        mocker.return_value = mocked_response
        currency_convertor = CurrencyConvertor()
        with pytest.raises(CurrencyAPIException):
            currency_convertor.get_currency_rates("USD", "EUR", None)
    assert "Currency API request failed" in caplog.text


def test_http_error_429_maps_to_currency_api_exception(caplog):
    """urllib raises HTTPError on 429; client maps to CurrencyAPIException and ERROR log."""
    caplog.set_level(logging.ERROR, logger="currencypy.currency_convertor")
    body = b'{"success":false,"error":{"code":429,"info":"too many requests"}}'
    http_exc = urllib.error.HTTPError(
        "http://api.example/live",
        429,
        "Too Many Requests",
        {},
        BytesIO(body),
    )
    with patch("currencypy.currency_convertor.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = http_exc
        currency_convertor = CurrencyConvertor()
        with pytest.raises(CurrencyAPIException):
            currency_convertor.get_currency_rates("USD", "EUR", None)
    assert "Currency API request failed" in caplog.text


def test_urlerror_maps_to_currency_api_exception(caplog):
    """Network failures become APIResponse and CurrencyAPIException."""
    caplog.set_level(logging.ERROR, logger="currencypy.currency_convertor")
    with patch("currencypy.currency_convertor.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("connection reset")
        currency_convertor = CurrencyConvertor()
        with pytest.raises(CurrencyAPIException):
            currency_convertor.get_currency_rates("USD", "EUR", None)
    assert "Currency API request failed" in caplog.text


def test_http_429_retries_then_success():
    """With api_max_retries=1, one 429 then a 200 response succeeds."""
    ok_body = json.dumps(
        {
            "success": True,
            "quotes": {"USDEUR": 0.92},
        }
    ).encode()
    ok_resp = MagicMock()
    ok_resp.read.return_value = ok_body
    ok_resp.status = 200
    ok_resp.headers = {}
    ok_cm = MagicMock()
    ok_cm.__enter__ = MagicMock(return_value=ok_resp)
    ok_cm.__exit__ = MagicMock(return_value=False)

    first = urllib.error.HTTPError(
        "http://api.example/live",
        429,
        "Too Many Requests",
        {"Retry-After": "0"},
        BytesIO(b"{}"),
    )

    with (
        patch(
            "currencypy.currency_convertor.urllib.request.urlopen",
            side_effect=[first, ok_cm],
        ) as mock_urlopen,
        patch("currencypy.currency_convertor.time.sleep") as mock_sleep,
    ):
        currency_convertor = CurrencyConvertor(api_max_retries=1)
        rate = currency_convertor.get_currency_rates("USD", "EUR", None)
    assert rate == Decimal("0.92")
    assert mock_urlopen.call_count == 2
    mock_sleep.assert_called_once()
