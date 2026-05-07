# converters/__init__.py
"""Engine abstraction layer for anyfile2md."""

from .base import BaseConverter, ConversionResult
from .markitdown import MarkitdownConverter

__all__ = [
    "BaseConverter",
    "ConversionResult",
    "MarkitdownConverter",
]