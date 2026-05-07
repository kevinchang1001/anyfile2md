# skills/anyfile2md/scripts/converters/mineru.py
"""MinerU converter implementation (stub)."""

from pathlib import Path

from .base import BaseConverter, ConversionResult


class MineruConverter(BaseConverter):
    """
    Converter using MinerU for complex PDFs.

    STUB: This is not yet implemented.
    """

    @property
    def name(self) -> str:
        return "mineru"

    @property
    def priority(self) -> int:
        """MinerU has lower priority than markitdown."""
        return 20

    def is_available(self) -> bool:
        """
        Check if MinerU is installed.

        STUB: Always returns False until implemented.
        """
        return False

    def can_handle(self, file_path: str) -> float:
        """
        MinerU excels at complex PDFs.

        STUB: Returns 0.0 until implemented.
        """
        return 0.0

    def convert(self, input_path: str, output_path: str) -> ConversionResult:
        """
        Convert file using MinerU.

        STUB: Not yet implemented.
        """
        return ConversionResult(
            success=False,
            engine=self.name,
            error="MinerU converter not yet implemented"
        )