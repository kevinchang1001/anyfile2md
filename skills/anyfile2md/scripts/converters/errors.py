# skills/anyfile2md/scripts/converters/errors.py
"""Error handling and error templates for converters."""

from dataclasses import dataclass, field
from typing import Optional


class ConversionError(Exception):
    """
    Error during conversion with helpful solutions.

    Attributes:
        engine: Name of the engine that failed
        reason: Why the conversion failed
        solutions: List of potential solutions to try
    """

    def __init__(self, engine: str, reason: str, solutions: Optional[list[str]] = None):
        self.engine = engine
        self.reason = reason
        self.solutions = solutions or []
        super().__init__(str(self))

    def __str__(self) -> str:
        parts = [f"错误: {self.engine} 转换失败"]
        parts.append(f"原因: {self.reason}")
        if self.solutions:
            parts.append("\n解决方案:")
            for i, solution in enumerate(self.solutions, 1):
                parts.append(f"  {i}. {solution}")
        return "\n".join(parts)


@dataclass
class ConversionAttempt:
    """Record of a single conversion attempt."""
    engine: str
    success: bool
    error: Optional[str] = None
    quality_score: int = 0


@dataclass
class ConversionSession:
    """
    Record of an entire conversion session with multiple attempts.
    """
    file_path: str
    attempts: list[ConversionAttempt] = field(default_factory=list)
    final_result: Optional[str] = None
    final_engine: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON logging."""
        return {
            "file": self.file_path,
            "attempts": [
                {
                    "engine": a.engine,
                    "success": a.success,
                    "error": a.error,
                    "quality_score": a.quality_score,
                }
                for a in self.attempts
            ],
            "final_result": self.final_result,
            "final_engine": self.final_engine,
        }


class ErrorTemplate:
    """Provides error templates and solutions for common errors."""

    @staticmethod
    def for_engine(engine_name: str) -> str:
        """Get error template for an engine."""
        templates = {
            "markitdown": (
                "MarkItDown not found or not working.\n"
                "Solutions:\n"
                "  1. Install: pip install markitdown\n"
                "  2. Or run: bash scripts/install_deps.sh"
            ),
            "mineru": (
                "MinerU not available or API error.\n"
                "Solutions:\n"
                "  1. Install: pip install mineru\n"
                "  2. Check GPU availability\n"
                "  3. Use CPU mode if GPU not available"
            ),
        }
        return templates.get(engine_name, f"Unknown engine: {engine_name}")

    @staticmethod
    def for_error(error_msg: str) -> list[str]:
        """Suggest solutions based on error message."""
        solutions = []

        if "GPU" in error_msg or "CUDA" in error_msg:
            solutions.append("GPU not available - consider using CPU mode")

        if "timeout" in error_msg.lower():
            solutions.append("Conversion timeout - try with larger timeout")

        if "not found" in error_msg.lower():
            solutions.append("Install the required dependency")

        if not solutions:
            solutions.append("Check the error details above")

        return solutions