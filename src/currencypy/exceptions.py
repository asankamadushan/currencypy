"""
Currency exceptions module.
"""

from typing import Dict, Union, Any


class CurrencyAPIException(Exception):
    """
    CurrencyAPIException class
    """

    def __init__(self, message, error: Union[Dict[str, Any], None] = None):
        """
        Constructor
        Args:
            message (str): Message
            error (dict): Error
        """
        self.message = message
        self.error = error
        super().__init__(message)


class CurrencyAPIKeyException(Exception):
    """
    CurrencyAPIKeyException class
    """


class CurrencyException(Exception):
    """
    CurrencyException class
    """
