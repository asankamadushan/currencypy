"""
Currency Convertor module
"""

import logging
import os
import random
import time
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from typing import Union

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from dotenv import load_dotenv

from cachetools import LRUCache, TTLCache
from currencypy.exceptions import (
    CurrencyAPIException,
    CurrencyAPIKeyException,
    CurrencyException,
)
from currencypy.money import Money

logger = logging.getLogger(__name__)


def _parse_error_response_body(http_code: int, body: bytes) -> dict:
    """Parse JSON error body or return a synthetic dict for logging and _raise_api_error."""
    if not body.strip():
        return {
            "success": False,
            "error": {"code": http_code, "info": "empty response body"},
        }
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            parsed["success"] = False
            return parsed
    except json.JSONDecodeError:
        pass
    text = body.decode("utf-8", errors="replace")[:500]
    return {
        "success": False,
        "error": {"code": http_code, "info": text},
    }


def _retry_after_seconds(headers: dict[str, str]) -> float | None:
    """Return seconds to wait from Retry-After, or None to use backoff."""
    raw = headers.get("Retry-After")
    if raw is None:
        return None
    raw = raw.strip()
    try:
        return float(raw)
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = (dt - datetime.now(timezone.utc)).total_seconds()
    return max(0.0, float(delta))


@dataclass
class APIResponse:
    """The API response dataclass."""

    status_code: int
    success: bool
    data: dict
    headers: dict


class APIRequestHandler:
    """The HTTP Api request handler class."""

    _default_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    _default_key_name = "access_key"

    def __init__(
        self,
        base_url: str,
        api_key: Union[str, None] = None,
        headers: Union[dict[str, str], None] = None,
        *,
        max_retries: int = 0,
        retry_base_seconds: float = 1.0,
        retry_max_sleep_seconds: float = 60.0,
    ):
        """The constructor method.
        Args:
            api_key (str): The API key.
            base_url (str): The base URL of the API.
            headers (Union[Dict[str, str], None], optional): The headers. Defaults to
                    None.
            max_retries: Extra attempts for HTTP 429 / 503 after the first request.
            retry_base_seconds: Base delay for exponential backoff when Retry-After
                is absent.
            retry_max_sleep_seconds: Upper bound for sleep between retries.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = headers.copy() if headers else self._default_headers
        if self.api_key:
            self.headers[self._default_key_name] = self.api_key
        self.max_retries = max_retries
        self.retry_base_seconds = retry_base_seconds
        self.retry_max_sleep_seconds = retry_max_sleep_seconds

    def get(
        self, path: str, params: dict[str, Union[str, int]] | None = None
    ) -> APIResponse:
        """The HTTP GET request method.
        Args:
            path (str): The path of the API endpoint.
            params (Dict[str, Union[str, int]]): The query params.
        Returns:
            APIResponse: Parsed response; ``success`` is False for HTTP errors and
            network failures (see ``status_code``).

        Note:
            HTTP error responses (4xx/5xx) and ``URLError`` are converted to
            ``APIResponse`` instead of raising. Callers such as ``CurrencyConvertor``
            map failures to ``CurrencyAPIException``.
        """
        url = urllib.parse.urljoin(self.base_url, path)
        if not params:
            copy_params = {}
        else:
            copy_params = params.copy()

        if self.api_key:
            copy_params[self._default_key_name] = self.api_key
        safe_param_keys = sorted(k for k in copy_params if k != self._default_key_name)
        logger.debug("HTTP GET path=%s param_keys=%s", path, safe_param_keys)
        encoded_params = urllib.parse.urlencode(copy_params)
        url = f"{url}?{encoded_params}"

        max_attempts = self.max_retries + 1
        attempt = 0
        result: APIResponse | None = None

        while attempt < max_attempts:
            attempt += 1
            try:
                with urllib.request.urlopen(url) as response:
                    raw = response.read()
                    status = response.status
                    resp_headers = dict(response.headers.items())
                    if status == 200:
                        result = APIResponse(
                            status_code=status,
                            success=True,
                            data=json.loads(raw),
                            headers=resp_headers,
                        )
                    else:
                        data = _parse_error_response_body(status, raw)
                        result = APIResponse(
                            status_code=status,
                            success=False,
                            data=data,
                            headers=resp_headers,
                        )
                    break
            except urllib.error.HTTPError as e:
                body = e.read()
                hdrs = dict(e.headers.items()) if e.headers else {}
                if e.code in (429, 503) and attempt < max_attempts:
                    wait = _retry_after_seconds(hdrs)
                    if wait is None:
                        wait = min(
                            self.retry_max_sleep_seconds,
                            self.retry_base_seconds * (2 ** (attempt - 1))
                            + random.uniform(0, 0.25),
                        )
                    else:
                        wait = min(wait, self.retry_max_sleep_seconds)
                    logger.warning(
                        "HTTP GET path=%s status=%s retry %s/%s sleep=%.2fs",
                        path,
                        e.code,
                        attempt,
                        max_attempts,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                result = APIResponse(
                    status_code=e.code,
                    success=False,
                    data=_parse_error_response_body(e.code, body),
                    headers=hdrs,
                )
                break
            except urllib.error.URLError as e:
                result = APIResponse(
                    status_code=0,
                    success=False,
                    data={
                        "success": False,
                        "error": {"info": str(e.reason)},
                    },
                    headers={},
                )
                break

        assert result is not None
        logger.debug(
            "HTTP response path=%s status_code=%s success=%s",
            path,
            result.status_code,
            result.success,
        )
        if result.status_code != 200:
            logger.warning(
                "HTTP GET path=%s non-success status_code=%s success=%s",
                path,
                result.status_code,
                result.success,
            )
        return result


class CurrencyConvertor:
    """
    The currency conversion wrapper class.

    Diagnostic messages use the ``currencypy.currency_convertor`` logger (or
    configure the ``currencypy`` namespace). The library does not configure
    handlers; set levels and handlers in the application.
    """

    _BASE_URL = "https://api.currencylayer.com/"
    _LIVE_URL = "live"
    _HISTORICAL_URL = "historical"
    _SUPPORTED_LIST_URL = "list"
    _DEFAULT_CURRENCY_LIST = {
        "AED": "United Arab Emirates Dirham",
        "AFN": "Afghan Afghani",
        "ALL": "Albanian Lek",
        "AMD": "Armenian Dram",
        "ANG": "Netherlands Antillean Guilder",
        "AOA": "Angolan Kwanza",
        "ARS": "Argentine Peso",
        "AUD": "Australian Dollar",
        "AWG": "Aruban Florin",
        "AZN": "Azerbaijani Manat",
        "BAM": "Bosnia-Herzegovina Convertible Mark",
        "BBD": "Barbadian Dollar",
        "BDT": "Bangladeshi Taka",
        "BGN": "Bulgarian Lev",
        "BHD": "Bahraini Dinar",
        "BIF": "Burundian Franc",
        "BMD": "Bermudan Dollar",
        "BND": "Brunei Dollar",
        "BOB": "Bolivian Boliviano",
        "BRL": "Brazilian Real",
        "BSD": "Bahamian Dollar",
        "BTC": "Bitcoin",
        "BTN": "Bhutanese Ngultrum",
        "BWP": "Botswanan Pula",
        "BYN": "New Belarusian Ruble",
        "BYR": "Belarusian Ruble",
        "BZD": "Belize Dollar",
        "CAD": "Canadian Dollar",
        "CDF": "Congolese Franc",
        "CHF": "Swiss Franc",
        "CLF": "Chilean Unit of Account (UF)",
        "CLP": "Chilean Peso",
        "CNY": "Chinese Yuan",
        "COP": "Colombian Peso",
        "CRC": "Costa Rican Colón",
        "CUC": "Cuban Convertible Peso",
        "CUP": "Cuban Peso",
        "CVE": "Cape Verdean Escudo",
        "CZK": "Czech Republic Koruna",
        "DJF": "Djiboutian Franc",
        "DKK": "Danish Krone",
        "DOP": "Dominican Peso",
        "DZD": "Algerian Dinar",
        "EGP": "Egyptian Pound",
        "ERN": "Eritrean Nakfa",
        "ETB": "Ethiopian Birr",
        "EUR": "Euro",
        "FJD": "Fijian Dollar",
        "FKP": "Falkland Islands Pound",
        "GBP": "British Pound Sterling",
        "GEL": "Georgian Lari",
        "GGP": "Guernsey Pound",
        "GHS": "Ghanaian Cedi",
        "GIP": "Gibraltar Pound",
        "GMD": "Gambian Dalasi",
        "GNF": "Guinean Franc",
        "GTQ": "Guatemalan Quetzal",
        "GYD": "Guyanaese Dollar",
        "HKD": "Hong Kong Dollar",
        "HNL": "Honduran Lempira",
        "HRK": "Croatian Kuna",
        "HTG": "Haitian Gourde",
        "HUF": "Hungarian Forint",
        "IDR": "Indonesian Rupiah",
        "ILS": "Israeli New Sheqel",
        "IMP": "Manx pound",
        "INR": "Indian Rupee",
        "IQD": "Iraqi Dinar",
        "IRR": "Iranian Rial",
        "ISK": "Icelandic Króna",
        "JEP": "Jersey Pound",
        "JMD": "Jamaican Dollar",
        "JOD": "Jordanian Dinar",
        "JPY": "Japanese Yen",
        "KES": "Kenyan Shilling",
        "KGS": "Kyrgystani Som",
        "KHR": "Cambodian Riel",
        "KMF": "Comorian Franc",
        "KPW": "North Korean Won",
        "KRW": "South Korean Won",
        "KWD": "Kuwaiti Dinar",
        "KYD": "Cayman Islands Dollar",
        "KZT": "Kazakhstani Tenge",
        "LAK": "Laotian Kip",
        "LBP": "Lebanese Pound",
        "LKR": "Sri Lankan Rupee",
        "LRD": "Liberian Dollar",
        "LSL": "Lesotho Loti",
        "LTL": "Lithuanian Litas",
        "LVL": "Latvian Lats",
        "LYD": "Libyan Dinar",
        "MAD": "Moroccan Dirham",
        "MDL": "Moldovan Leu",
        "MGA": "Malagasy Ariary",
        "MKD": "Macedonian Denar",
        "MMK": "Myanma Kyat",
        "MNT": "Mongolian Tugrik",
        "MOP": "Macanese Pataca",
        "MRO": "Mauritanian Ouguiya",
        "MUR": "Mauritian Rupee",
        "MVR": "Maldivian Rufiyaa",
        "MWK": "Malawian Kwacha",
        "MXN": "Mexican Peso",
        "MYR": "Malaysian Ringgit",
        "MZN": "Mozambican Metical",
        "NAD": "Namibian Dollar",
        "NGN": "Nigerian Naira",
        "NIO": "Nicaraguan Córdoba",
        "NOK": "Norwegian Krone",
        "NPR": "Nepalese Rupee",
        "NZD": "New Zealand Dollar",
        "OMR": "Omani Rial",
        "PAB": "Panamanian Balboa",
        "PEN": "Peruvian Nuevo Sol",
        "PGK": "Papua New Guinean Kina",
        "PHP": "Philippine Peso",
        "PKR": "Pakistani Rupee",
        "PLN": "Polish Zloty",
        "PYG": "Paraguayan Guarani",
        "QAR": "Qatari Rial",
        "RON": "Romanian Leu",
        "RSD": "Serbian Dinar",
        "RUB": "Russian Ruble",
        "RWF": "Rwandan Franc",
        "SAR": "Saudi Riyal",
        "SBD": "Solomon Islands Dollar",
        "SCR": "Seychellois Rupee",
        "SDG": "Sudanese Pound",
        "SEK": "Swedish Krona",
        "SGD": "Singapore Dollar",
        "SHP": "Saint Helena Pound",
        "SLL": "Sierra Leonean Leone",
        "SOS": "Somali Shilling",
        "SRD": "Surinamese Dollar",
        "STD": "São Tomé and Príncipe Dobra",
        "SVC": "Salvadoran Colón",
        "SYP": "Syrian Pound",
        "SZL": "Swazi Lilangeni",
        "THB": "Thai Baht",
        "TJS": "Tajikistani Somoni",
        "TMT": "Turkmenistani Manat",
        "TND": "Tunisian Dinar",
        "TOP": "Tongan Paʻanga",
        "TRY": "Turkish Lira",
        "TTD": "Trinidad and Tobago Dollar",
        "TWD": "New Taiwan Dollar",
        "TZS": "Tanzanian Shilling",
        "UAH": "Ukrainian Hryvnia",
        "UGX": "Ugandan Shilling",
        "USD": "United States Dollar",
        "UYU": "Uruguayan Peso",
        "UZS": "Uzbekistan Som",
        "VEF": "Venezuelan Bolívar Fuerte",
        "VND": "Vietnamese Dong",
        "VUV": "Vanuatu Vatu",
        "WST": "Samoan Tala",
        "XAF": "CFA Franc BEAC",
        "XAG": "Silver (troy ounce)",
        "XAU": "Gold (troy ounce)",
        "XCD": "East Caribbean Dollar",
        "XDR": "Special Drawing Rights",
        "XOF": "CFA Franc BCEAO",
        "XPF": "CFP Franc",
        "YER": "Yemeni Rial",
        "ZAR": "South African Rand",
        "ZMK": "Zambian Kwacha (pre-2013)",
        "ZMW": "Zambian Kwacha",
        "ZWL": "Zimbabwean Dollar",
    }

    def __init__(
        self,
        api_key: Union[str, None] = None,
        live_update: bool = False,
        *,
        live_rate_ttl_seconds: int = 300,
        rate_cache_maxsize: int = 1000,
        api_max_retries: int = 0,
        api_retry_base_seconds: float = 1.0,
        api_retry_max_sleep_seconds: float = 60.0,
    ) -> None:
        """
        Initialize the currency convertor.
        args:
            api_key: The API key to use.
            live_update: If this is true the supported currency list
                        will be check against the API response.
            live_rate_ttl_seconds: Time-to-live for cached live (non-historical) rates.
            rate_cache_maxsize: Max entries for live TTL cache and historical LRU cache.
            api_max_retries: Extra HTTP attempts for 429/503 from the currency API.
            api_retry_base_seconds: Backoff base when Retry-After is not set.
            api_retry_max_sleep_seconds: Cap on sleep between API retries.
        """
        self.api_key = api_key or self.__load_api_key_from_env()
        self.live_update = live_update
        self.api_service = APIRequestHandler(
            base_url=self._BASE_URL,
            api_key=self.api_key,
            max_retries=api_max_retries,
            retry_base_seconds=api_retry_base_seconds,
            retry_max_sleep_seconds=api_retry_max_sleep_seconds,
        )
        self._supported_currencies = self.get_supported_currencies(live_update)
        self._live_rate_cache: TTLCache[tuple[str, str, datetime | None], Decimal] = (
            TTLCache(maxsize=rate_cache_maxsize, ttl=live_rate_ttl_seconds)
        )
        self._historical_rate_cache: LRUCache[
            tuple[str, str, datetime | None], Decimal
        ] = LRUCache(maxsize=rate_cache_maxsize)

    @staticmethod
    def __load_api_key_from_env() -> str:
        """
        Load api key from the environment variable CL_API_KEY.
        return:
            The API key.
        """
        load_dotenv()
        key = os.environ.get("CL_API_KEY")
        if key is None:
            raise CurrencyAPIKeyException(
                "CL_API_KEY is not set in the environment variable."
            )
        return key

    def _fetch_supported_currencies(self) -> dict[str, str]:
        """
        Fetch the supported currencies from the API.
        returns:
            The supported currencies.
        """
        logger.debug("Fetching supported currencies")
        response = self.api_service.get(self._SUPPORTED_LIST_URL)

        if not response.success or response.data["success"] is False:
            self._raise_api_error(response)

        return response.data["currencies"]

    def _fetch_live_currency_rates(self, from_currency: str, to_currency: str) -> dict:
        """
        Fetch the currency rates from the API.
        args:
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.
        returns:
            The currency rates.
        """
        logger.debug(
            "Fetching live currency rates for %s to %s", from_currency, to_currency
        )
        response = self.api_service.get(
            self._LIVE_URL,
            params={"source": from_currency, "access_key": self.api_key},
        )

        if not response.success or response.data["success"] is False:
            self._raise_api_error(response)

        return response.data

    def _fetch_historical_currency_rates(
        self, from_currency: str, to_currency: str, date: datetime
    ) -> dict:
        """
        Fetch the currency rates from the API.
        args:
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.
            date: The date to fetch the rates for.
        returns:
            The currency rates.
        """
        logger.debug(
            "Fetching historical currency rates for %s to %s on %s",
            from_currency,
            to_currency,
            date,
        )
        response = self.api_service.get(
            self._HISTORICAL_URL,
            params={
                "access_key": self.api_key,
                "source": from_currency,
                "currencies": to_currency,
                "date": date.strftime("%Y-%m-%d"),
            },
        )
        if not response.success or response.data["success"] is False:
            self._raise_api_error(response)

        return response.data

    @staticmethod
    def _raise_api_error(response: APIResponse):
        error = response.data.get("error") if response.data else None
        logger.error(
            "Currency API request failed: status_code=%s api_error=%s",
            response.status_code,
            error,
        )
        raise CurrencyAPIException("Error getting currencies", error)

    def get_supported_currencies(self, live_update=False) -> dict[str, str]:
        """
        Get the supported currencies.
        args:
            live_update: Whether to update the supported currencies.
        returns:
            The supported currencies.
        """
        if live_update:
            return self._fetch_supported_currencies()
        return self._DEFAULT_CURRENCY_LIST

    def get_currency_rates(
        self, from_currency: str, to_currency: str, date: Union[datetime, None] = None
    ) -> Decimal:
        """
        Get the currency rates for a given currency pair.
        args:
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.
            date: The date to fetch the rates for.
        returns:
            The currency rate.
        raises:
            CurrencyException: If the currency is not supported.
            CurrencyAPIException: If there is an error fetching the rates.
        """
        if from_currency not in self._supported_currencies:
            logger.debug("Unsupported source currency: %s", from_currency)
            raise CurrencyException(f"{from_currency} is not a supported currency")
        if to_currency not in self._supported_currencies:
            logger.debug("Unsupported target currency: %s", to_currency)
            raise CurrencyException(f"{to_currency} is not a supported currency")

        key = (from_currency, to_currency, date)
        cache = self._live_rate_cache if date is None else self._historical_rate_cache
        if key in cache:
            logging.info("Cache hit for %s", key)
            return cache[key]

        logging.info("Cache miss for %s", key)
        logger.debug(
            "Resolving rate %s -> %s date=%s",
            from_currency,
            to_currency,
            date,
        )
        if date:
            rates = self._fetch_historical_currency_rates(
                from_currency, to_currency, date
            )
        else:
            rates = self._fetch_live_currency_rates(from_currency, to_currency)

        quote = rates["quotes"][f"{from_currency}{to_currency}"]
        result = Decimal(str(quote))
        cache[key] = result
        return result

    def convert(
        self,
        money: Money,
        *,
        to_currency: str = "USD",
        date: Union[datetime, None] = None,
    ) -> Money:
        """
        Convert a monetary amount from one currency to another.
        args:
            money: The money to convert (amount and source currency).
            to_currency: The currency to convert to.
            date: The date to fetch the rates for.

        returns:
            The converted money in to_currency.

        raises:
            CurrencyException: If the currency is not supported.
            CurrencyAPIException: If there is an error fetching the rates.

        Convert between different currencies on a given date rate.
        >>> from decimal import Decimal
        >>> from currencypy.money import Money
        >>> c = CurrencyConvertor()
        >>> c.convert(Money(Decimal("100"), "USD"), to_currency="LKR",
        ...           date=datetime(2019, 1, 1))
        Money(amount=Decimal('18283.9983'), currency='LKR')

        Convert between same currencies.
        >>> c = CurrencyConvertor()
        >>> c.convert(Money(Decimal("100"), "USD"), to_currency="USD")
        Money(amount=Decimal('100'), currency='USD')
        """
        if money.currency == to_currency:
            logger.debug("convert skipped (same currency): %s", to_currency)
            return money

        logger.debug(
            "convert %s -> %s date=%s",
            money.currency,
            to_currency,
            date,
        )
        rate = self.get_currency_rates(money.currency, to_currency, date)
        return Money(money.amount * rate, to_currency)


if __name__ == "__main__":
    c = CurrencyConvertor(live_update=True)
    try:
        i = 0
        while i < 10:
            x = c.convert(Money(Decimal("100"), "USD"), to_currency="LKR")
            i += 1

        x = c.convert(Money(Decimal("100"), "USD"), to_currency="EUR")
        x = c.convert(
            Money(Decimal("100"), "USD"),
            to_currency="LKR",
            date=datetime(2019, 1, 1),
        )
    except CurrencyException as e:
        logger.error("CurrencyException: %s", e)
    except CurrencyAPIException as e:
        logger.error("CurrencyAPIException: %s", e)
    logger.info("All tests passed")
