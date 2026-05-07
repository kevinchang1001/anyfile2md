# converters/__init__.py
"""Engine abstraction layer for anyfile2md."""

from .base import BaseConverter, ConversionResult
from .markitdown import MarkitdownConverter
from .mineru import MineruConverter
from .registry import EngineRegistry, get_default_engine, select_best_engine

__all__ = [
    "BaseConverter",
    "ConversionResult",
    "MarkitdownConverter",
    "MineruConverter",
    "EngineRegistry",
    "get_default_engine",
    "select_best_engine",
]