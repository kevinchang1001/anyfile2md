# skills/anyfile2md/scripts/converters/registry.py
"""Engine registry for selecting the best converter."""

from typing import Optional, Tuple

from .base import BaseConverter
from .markitdown import MarkitdownConverter
from .mineru import MineruConverter


class EngineRegistry:
    """
    Registry of available converters.

    Singleton pattern ensures consistent engine selection.
    """

    _instance: Optional["EngineRegistry"] = None
    _engines: list[BaseConverter] = []

    def __new__(cls) -> "EngineRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_engines()
        return cls._instance

    def _initialize_engines(self) -> None:
        """Register all available engines."""
        self._engines = [
            MarkitdownConverter(),
            # MineruConverter(),  # Disabled until implemented
        ]

    def get_engine(self, name: str) -> Optional[BaseConverter]:
        """Get engine by name."""
        for engine in self._engines:
            if engine.name == name:
                return engine
        return None

    def select_engine(self, file_path: str) -> Tuple[BaseConverter, float]:
        """
        Select the best engine for a file.

        Returns (engine, confidence) tuple.
        """
        best_engine = None
        best_confidence = -1.0

        for engine in self._engines:
            if not engine.is_available():
                continue
            confidence = engine.can_handle(file_path)
            # Use priority as tiebreaker
            effective_score = confidence * 100 - engine.priority
            if effective_score > best_confidence:
                best_confidence = effective_score
                best_engine = engine

        if best_engine is None:
            # Fallback to markitdown
            best_engine = MarkitdownConverter()
            best_confidence = 0.0

        return best_engine, best_confidence

    def list_engines(self) -> list[str]:
        """List all registered engine names."""
        return [e.name for e in self._engines if e.is_available()]


# Module-level convenience function
def get_default_engine() -> BaseConverter:
    """Get the default engine (markitdown)."""
    return MarkitdownConverter()


def select_best_engine(file_path: str) -> Tuple[BaseConverter, float]:
    """Select best engine for file."""
    return EngineRegistry().select_engine(file_path)