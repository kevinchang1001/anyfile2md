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
            MineruConverter(),  # Now has real implementation
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
            # Pure confidence-based selection (priority is irrelevant for engine capability)
            if confidence > best_confidence:
                best_confidence = confidence
                best_engine = engine

        if best_engine is None:
            fallback = MarkitdownConverter()
            if fallback.is_available():
                best_engine = fallback
                best_confidence = 0.0
            else:
                # No available engine at all
                return None, 0.0

        # Return actual confidence, not effective_score
        # (effective_score was only used for engine selection comparison)
        actual_confidence = best_engine.can_handle(file_path)
        return best_engine, actual_confidence

    def list_engines(self) -> list[str]:
        """List all registered engine names."""
        return [e.name for e in self._engines if e.is_available()]

    def get_available_engines(self) -> list[BaseConverter]:
        """Return all available engine instances."""
        return [e for e in self._engines if e.is_available()]


# Module-level convenience function
def get_default_engine() -> BaseConverter:
    """Get the default engine (markitdown)."""
    return MarkitdownConverter()


def select_best_engine(file_path: str) -> Tuple[BaseConverter, float]:
    """Select best engine for file."""
    return EngineRegistry().select_engine(file_path)