# converters/base.py
"""Base converter abstract class."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from .complexity import ComplexityDetector, get_detector
except ImportError:
    ComplexityDetector = None
    get_detector = None

logger = logging.getLogger(__name__)


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

    def __init__(self, detector=None):
        """
        Initialize converter with optional detector injection.

        Args:
            detector: A ComplexityDetector instance for complexity analysis.
                     If None, uses the global detector.
        """
        self._detector = detector

    @classmethod
    def set_detector(cls, detector):
        """
        DEPRECATED: Use constructor injection instead.

        Set the class-level detector for testing injection.

        Args:
            detector: A ComplexityDetector instance, or None to reset
        """
        # For backward compatibility, set on all existing instances
        # but prefer instance-level _detector
        cls._detector = detector

    @property
    @abstractmethod
    def name(self) -> str:
        """Converter name, e.g., 'markitdown', 'mineru'."""
        pass

    @property
    def priority(self) -> int:
        """Lower = higher priority. Default 50."""
        return 50

    def can_handle(self, file_path: str) -> float:
        """
        Return confidence (0.0-1.0) that this converter can handle the file.

        Default implementation uses complexity detection + engine-specific
        confidence mapping via _get_confidence().
        """
        ext = Path(file_path).suffix.lower()
        if ext != '.pdf':
            # Non-PDF files: use extension-based confidence
            return 0.0

        if ComplexityDetector is None or get_detector is None:
            return 0.5

        start_time = time.time()
        try:
            detector = self._detector or get_detector()
            result = detector.analyze(file_path)
            elapsed = time.time() - start_time
            if elapsed > 0.01:  # Log if > 10ms
                logger.debug(f"Complexity analysis: {elapsed:.3f}s for {file_path}")
            return self._get_confidence(result.score)
        except Exception:
            return 0.5

    @abstractmethod
    def _get_confidence(self, score: float) -> float:
        """
        Map complexity score to engine-specific confidence.

        Args:
            score: Complexity score from ComplexityDetector (0-10)

        Returns:
            Confidence value between 0 and 1
        """
        pass

    @abstractmethod
    def convert(self, input_path: str, output_path: str) -> ConversionResult:
        """Convert input file to output markdown."""
        pass

    def is_available(self) -> bool:
        """Check if converter is available (dependencies installed)."""
        return True