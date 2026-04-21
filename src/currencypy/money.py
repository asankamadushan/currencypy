"""
Money value type: decimal amount with ISO currency code.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """A monetary amount in a given currency."""

    amount: Decimal
    currency: str
