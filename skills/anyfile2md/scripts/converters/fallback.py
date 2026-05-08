# skills/anyfile2md/scripts/converters/fallback.py
"""Fallback handler for multi-engine conversion with automatic retry."""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

from .base import BaseConverter, ConversionResult
from .errors import ConversionSession, ConversionAttempt
from .registry import EngineRegistry, get_registry


logger = logging.getLogger(__name__)


class FallbackHandler:
    """
    Handles conversion with automatic fallback between engines.

    When the primary engine fails, automatically tries the next available
    engine based on confidence order.
    """

    def __init__(self, registry: EngineRegistry = None, max_attempts: int = 2):
        """
        Initialize FallbackHandler.

        Args:
            registry: Engine registry to use (default: global singleton)
            max_attempts: Maximum number of engines to try (default: 2)
        """
        self.max_attempts = max_attempts
        self.registry = registry or get_registry()

    def get_available_engines(self) -> list[BaseConverter]:
        """Get all available engines (unsorted, sorting happens in convert_with_fallback)."""
        return self.registry.get_available_engines()

    def _get_sorted_engines(
        self,
        input_path: str,
        preferred_engine: Optional[str] = None
    ) -> list[BaseConverter]:
        """
        Get engines sorted by confidence, with preferred engine at front if specified.

        Args:
            input_path: File path for confidence evaluation
            preferred_engine: Optional engine name to prioritize

        Returns:
            Sorted list of engines
        """
        engines = self.get_available_engines()
        if not engines:
            return []

        # Sort engines by confidence for this file
        def get_confidence(engine: BaseConverter) -> float:
            return engine.can_handle(input_path)

        engines = sorted(engines, key=get_confidence, reverse=True)

        # If preferred_engine is specified, move it to the front
        if preferred_engine:
            preferred = self.registry.get_engine(preferred_engine)
            if preferred and preferred.is_available() and preferred in engines:
                engines.remove(preferred)
                engines.insert(0, preferred)
                logger.info(f"Preferred engine '{preferred_engine}' moved to front")

        return engines

    def _attempt_conversion(
        self,
        engine: BaseConverter,
        input_path: str,
        output_path: str
    ) -> Tuple[ConversionAttempt, ConversionResult]:
        """
        Attempt conversion with a single engine.

        Args:
            engine: Converter engine to use
            input_path: Input file path
            output_path: Output file path

        Returns:
            Tuple of (ConversionAttempt, ConversionResult)
        """
        attempt = ConversionAttempt(engine=engine.name)

        try:
            result = engine.convert(input_path, output_path)
            attempt.success = result.success
            attempt.error = result.error
            attempt.quality_score = result.quality_score
            return attempt, result

        except Exception as e:
            attempt.success = False
            attempt.error = str(e)
            result = ConversionResult(
                success=False,
                engine=engine.name,
                error=str(e)
            )
            return attempt, result

    def _write_log(self, session: ConversionSession, log_file: str) -> None:
        """Write session to log file."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(session.to_dict()) + "\n")

    def convert_with_fallback(
        self,
        input_path: str,
        output_path: str,
        preferred_engine: Optional[str] = None,
        log_file: Optional[str] = None
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
        engines = self._get_sorted_engines(input_path, preferred_engine)

        if not engines:
            result = ConversionResult(
                success=False,
                engine="none",
                error="No conversion engines available"
            )
            session.final_result = "failed"
            return result, session

        # Try each engine in order
        for engine in engines[:self.max_attempts]:
            attempt, result = self._attempt_conversion(engine, input_path, output_path)
            session.attempts.append(attempt)

            if result.success:
                session.final_result = "success"
                session.final_engine = engine.name
                logger.info(
                    f"Successfully converted {input_path} with {engine.name}"
                )
                if log_file:
                    self._write_log(session, log_file)
                return result, session

            logger.warning(f"Engine {engine.name} failed: {result.error}")

        # All engines failed
        session.final_result = "failed"
        first_error = session.attempts[0].error if session.attempts else "Unknown error"
        result = ConversionResult(
            success=False,
            engine=session.attempts[-1].engine if session.attempts else "unknown",
            error=f"All engines failed. Last error: {first_error}"
        )

        if log_file:
            self._write_log(session, log_file)

        return result, session

    def get_best_engine(self, file_path: str) -> Tuple[BaseConverter, float]:
        """Get the best engine for a file."""
        return self.registry.select_engine(file_path)