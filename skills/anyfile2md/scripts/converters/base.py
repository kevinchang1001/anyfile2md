# converters/base.py
"""Base converter abstract class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    success: bool
    output_path: Optional[str] = None
    engine: str = ""
    quality_score: int = 0
    error: Optional[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class BaseConverter(ABC):
    """Abstract base class for file converters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Converter name, e.g., 'markitdown', 'mineru'."""
        pass

    @property
    def priority(self) -> int:
        """Lower = higher priority. Default 50."""
        return 50

    @abstractmethod
    def can_handle(self, file_path: str) -> float:
        """
        Return confidence (0.0-1.0) that this converter can handle the file.
        0.0 = cannot handle, 1.0 = perfect match.
        """
        pass

    @abstractmethod
    def convert(self, input_path: str, output_path: str) -> ConversionResult:
        """Convert input file to output markdown."""
        pass

    def is_available(self) -> bool:
        """Check if converter is available (dependencies installed)."""
        return True