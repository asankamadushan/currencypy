"""
Currency Convertor module
"""
import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, Union

import json
import urllib
import urllib.parse
import urllib.request
from dataclasses import dataclass
from dotenv import load_dotenv
from currencypy.exceptions import (
    CurrencyAPIException,
    CurrencyAPIKeyException,
    CurrencyException,
)


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
    _default_key_name = "apikey"

    def __init__(
        self,
        base_url: str,
        api_key: Union[str, None] = None,
        headers: Union[Dict[str, str], None] = None,
    ):
        """The constructor method.
        Args:
            api_key (str): The API key.
            base_url (str): The base URL of the API.
            headers (Union[Dict[str, str], None], optional): The headers. Defaults to
                    None.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = headers.copy() if headers else self._default_headers
        if self.api_key:
            self.headers[self._default_key_name] = self.api_key

    def get(self, path: str, params: Dict[str, Union[str, int]]) -> APIResponse:
        """The HTTP GET request method.
        Args:
            path (str): The path of the API endpoint.
            params (Dict[str, Union[str, int]]): The query params.
        Returns:
            Dict[str, Union[str, int]]: The response data.

        Raises:
            CurrencyAPIException: If the response status is not in range 200-299.
        """
        url = self._get_url(path)
        q_params = self._get_query_params(params)
        url = f"{url}?{q_params}"
        with urllib.request.urlopen(url) as response:
            if response.status in range(200, 299):
                return APIResponse(
                    status_code=response.status,
                    success=True,
                    data=json.loads(response.read()),
                    headers=response.headers,
                )
            elif response.status in range(400, 499):
                return APIResponse(
                    status_code=response.status,
                    success=False,
                    data=json.loads(response.read()),
                    headers=response.headers,
                )
            else:
                return APIResponse(
                    status_code=response.status,
                    success=False,
                    data={"error": "Something went wrong"},
                    headers=response.headers,
                )

    @staticmethod
    def _get_query_params(params: dict[str, Union[str, int]]) -> str:
        """The query params builder method.
        Args:
            params (Dict[str, Union[str, int]]): The query params.
        """
        return urllib.parse.urlencode(params)

    def _get_url(self, path: str) -> str:
        """The URL builder method.
        Args:
            path (str): The path of the API endpoint.
        """
        return urllib.parse.urljoin(self.base_url, path)


class CurrencyConvertor:
    """
    The currency conversion wrapper class.
    """

    _BASE_URL = "http://api.currencylayer.com/"
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
        self, api_key: Union[str, None] = None, live_update: bool = False
    ) -> None:
        """
        Initialize the currency convertor.
        args:
            api_key: The API key to use.
            live_update: If this is true the supported currency list
                        will be check against the API response.
        """
        self.api_key = api_key or self.__load_api_key_from_env()
        self.live_update = live_update
        self.api_service = APIRequestHandler(
            base_url=self._BASE_URL, api_key=self.api_key
        )
        self._supported_currencies = self.get_supported_currencies(live_update)

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

    def _fetch_supported_currencies(self) -> Dict[str, str]:
        """
        Fetch the supported currencies from the API.
        returns:
            The supported currencies.
        """
        logging.debug("Fetching supported currencies")
        response = self.api_service.get(
            self._SUPPORTED_LIST_URL, params={"access_key": self.api_key}
        )

        if not response.success or response.data["success"] is False:
            self._raise_api_error(response)

        return response.data["currencies"]

    def _fetch_live_currency_rates(self, from_currency: str, to_currency: str) -> Dict:
        """
        Fetch the currency rates from the API.
        args:
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.
        returns:
            The currency rates.
        """
        logging.debug(
            "Fetching live currency rates for %s to %s", from_currency, to_currency
        )
        response = self.api_service.get(
            self._LIVE_URL,
            params={"source": from_currency},
        )

        if not response.success or response.data["success"] is False:
            self._raise_api_error(response)

        return response.data

    def _fetch_historical_currency_rates(
        self, from_currency: str, to_currency: str, date: datetime
    ) -> Dict:
        """
        Fetch the currency rates from the API.
        args:
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.
            date: The date to fetch the rates for.
        returns:
            The currency rates.
        """
        logging.debug(
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
        raise CurrencyAPIException("Error getting currencies", error)

    def get_supported_currencies(self, live_update=False) -> Dict[str, str]:
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

    @lru_cache(maxsize=1000)
    def get_currency_rates(
        self, from_currency: str, to_currency: str, date: datetime
    ) -> float:
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
            raise CurrencyException(f"{from_currency} is not a supported currency")
        if to_currency not in self._supported_currencies:
            raise CurrencyException(f"{to_currency} is not a supported currency")
        if date:
            rates = self._fetch_historical_currency_rates(
                from_currency, to_currency, date
            )
        else:
            rates = self._fetch_live_currency_rates(from_currency, to_currency)

        return rates["quotes"][f"{from_currency}{to_currency}"]

    def convert(
        self,
        amount: float,
        *,
        from_currency: str,
        to_currency: str = "USD",
        date: Union[datetime, None] = None,
    ) -> float:
        """
        Convert an amount from one currency to another.
        args:
            amount: The amount to convert.
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.
            date: The date to fetch the rates for.

        returns:
            The converted amount.

        raises:
            CurrencyException: If the currency is not supported.
            CurrencyAPIException: If there is an error fetching the rates.

        Convert between different currencies on a given date rate.
        >>> c = CurrencyConvertor()
        >>> c.convert(100.0, from_currency="USD", to_currency="LKR",
                        date=datetime(2019, 1, 1))
        18283.9983

        Convert between same currencies.
        >>> c = CurrencyConvertor()
        >>> c.convert(100.0, from_currency="USD", to_currency="USD")
        100.0
        """
        if from_currency == to_currency:
            return amount

        return amount * self.get_currency_rates(from_currency, to_currency, date)


if __name__ == "__main__":
    c = CurrencyConvertor(live_update=True)
    try:
        x = c.convert(
            100.0, from_currency="USD", to_currency="INR", date=datetime(2019, 1, 1)
        )
        x = c.convert(
            100.0, from_currency="USD", to_currency="LKR", date=datetime(2019, 1, 1)
        )
    except CurrencyException as e:
        print(e)
    except CurrencyAPIException as e:
        print(e)
    print("All tests passed")
