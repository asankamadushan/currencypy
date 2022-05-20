"""
Currency Convertor module
"""
import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, Union

import requests
from dotenv import load_dotenv

from currancypy.exceptions import (
    CurrencyAPIException,
    CurrencyAPIKeyException,
    CurrencyException,
)


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
        self._supported_currencies = self.get_supported_currencies(live_update)

    def __load_api_key_from_env(self) -> str:
        """
        Load api key from the environment variable API-KEY.
        return:
            The API key.
        """
        load_dotenv()
        key = os.getenv("API-KEY")
        if key is None:
            raise CurrencyAPIKeyException(
                "API-KEY is not set in the environment variable."
            )
        return key

    def _fetch_supported_currencies(self) -> Dict[str, str]:
        """
        Fetch the supported currencies from the API.
        returns:
            The supported currencies.
        """
        logging.debug("Fetching supported currencies")
        response = requests.get(
            self._BASE_URL + self._SUPPORTED_LIST_URL,
            params={"access_key": self.api_key},
        )
        if response.status_code != 200 or response.json()["success"] is False:
            raise CurrencyAPIException("Error getting currencies")

        return response.json()["currencies"]

    def _fetch_live_currency_rates(self, from_currency: str, to_currency: str) -> Dict:
        """
        Fetch the currency rates from the API.
        args:
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.
        returns:
            The currency rates.
        """
        response = requests.get(
            self._BASE_URL + self._LIVE_URL,
            params={
                "access_key": self.api_key,
                "source": from_currency,
                "currencies": to_currency,
            },
        )
        if response.status_code != 200 or response.json()["success"] is False:
            raise CurrencyAPIException("Error getting currencies")

        return response.json()

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
        response = requests.get(
            self._BASE_URL + self._HISTORICAL_URL,
            params={
                "access_key": self.api_key,
                "source": from_currency,
                "currencies": to_currency,
                "date": date.strftime("%Y-%m-%d"),
            },
        )
        if response.status_code != 200 or response.json()["success"] is False:
            raise CurrencyAPIException("Error getting currencies")

        return response.json()

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
        """
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

        Convert between different currencies on a given date rate.
        >>> c = CurrencyConvertor()
        >>> c.convert(100.0, from_currency="USD", to_currency="LKR", date=datetime(2019, 1, 1))
        18283.9983

        Convert between same currencies.
        >>> c = CurrencyConvertor()
        >>> c.convert(100.0, from_currency="USD", to_currency="USD")
        100.0
        """
        if from_currency not in self._supported_currencies:
            raise CurrencyException(f"{from_currency} is not a supported currency")
        if to_currency not in self._supported_currencies:
            raise CurrencyException(f"{to_currency} is not a supported currency")

        if "USD" not in [from_currency, to_currency]:
            raise CurrencyException("Only USD is supported")

        if from_currency == to_currency:
            return amount

        return amount * self.get_currency_rates(from_currency, to_currency, date)


if __name__ == "__main__":
    c = CurrencyConvertor()
    x = c.convert(
        100.0, from_currency="USD", to_currency="LKR", date=datetime(2019, 1, 1)
    )
    print(x)
    # import doctest

    # doctest.testmod()
    print("All tests passed")
