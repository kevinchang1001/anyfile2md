# skills/anyfile2md/scripts/converters/fallback.py
"""Fallback handler for multi-engine conversion with automatic retry."""

import logging
from typing import Optional, Tuple

from .base import BaseConverter, ConversionResult
from .errors import ConversionSession, ConversionAttempt
from .registry import EngineRegistry, select_best_engine


logger = logging.getLogger(__name__)


class FallbackHandler:
    """
    Handles conversion with automatic fallback between engines.

    When the primary engine fails, automatically tries the next available
    engine based on confidence order.
    """

    def __init__(self, max_attempts: int = 2):
        """
        Initialize FallbackHandler.

        Args:
            max_attempts: Maximum number of engines to try (default: 2)
        """
        self.max_attempts = max_attempts
        self.registry = EngineRegistry()

    def get_available_engines(self) -> list[BaseConverter]:
        """Get all available engines (unsorted, sorting happens in convert_with_fallback)."""
        return [e for e in self.registry._engines if e.is_available()]

    def convert_with_fallback(
        self,
        input_path: str,
        output_path: str,
        preferred_engine: Optional[str] = None
    ) -> Tuple[ConversionResult, ConversionSession]:
        """
        Attempt conversion with automatic fallback.

        Args:
            input_path: Path to input file
            output_path: Path for output markdown
            preferred_engine: Prefer this engine if available

        Returns:
            Tuple of (ConversionResult, ConversionSession) where ConversionResult
            is from the successful attempt (or final failure) and ConversionSession
            contains the full attempt history.
        """
        session = ConversionSession(file_path=input_path)
        engines = self.get_available_engines()

        if not engines:
            result = ConversionResult(
                success=False,
                engine="none",
                error="No conversion engines available"
            )
            session.final_result = "failed"
            return result, session

        # Sort engines by confidence for this file
        def get_confidence(engine: BaseConverter) -> float:
            return engine.can_handle(input_path)

        engines = sorted(engines, key=get_confidence, reverse=True)

        # Try each engine in order
        for engine in engines[:self.max_attempts]:
            attempt = ConversionAttempt(engine=engine.name)

            try:
                result = engine.convert(input_path, output_path)
                attempt.success = result.success
                attempt.error = result.error
                attempt.quality_score = result.quality_score

                session.attempts.append(attempt)

                if result.success:
                    session.final_result = "success"
                    session.final_engine = engine.name
                    logger.info(
                        f"Successfully converted {input_path} with {engine.name}"
                    )
                    return result, session
                else:
                    logger.warning(
                        f"Engine {engine.name} failed: {result.error}"
                    )
                    # Continue to next engine

            except Exception as e:
                attempt.success = False
                attempt.error = str(e)
                session.attempts.append(attempt)
                logger.warning(f"Engine {engine.name} raised exception: {e}")
                continue

        # All engines failed
        session.final_result = "failed"
        first_error = session.attempts[0].error if session.attempts else "Unknown error"
        result = ConversionResult(
            success=False,
            engine=session.attempts[-1].engine if session.attempts else "unknown",
            error=f"All engines failed. Last error: {first_error}"
        )
        return result, session

    def get_best_engine(self, file_path: str) -> Tuple[BaseConverter, float]:
        """Get the best engine for a file."""
        return select_best_engine(file_path)