# skills/anyfile2md/scripts/converters/markitdown.py
"""Markitdown converter implementation."""

import subprocess
from pathlib import Path

from .base import BaseConverter, ConversionResult
from .confidence import markitdown_confidence

MARKITDOWN_TIMEOUT = 60

# Module-level cache for availability check
_markitdown_available = None


class MarkitdownConverter(BaseConverter):
    """Converter using markitdown CLI."""

    @property
    def name(self) -> str:
        return "markitdown"

    @property
    def priority(self) -> int:
        """Markitdown has higher priority (lower number)."""
        return 10

    def __init__(self, detector=None):
        super().__init__(detector)

    def is_available(self) -> bool:
        """Check if markitdown is installed (cached)."""
        global _markitdown_available
        if _markitdown_available is None:
            _markitdown_available = subprocess.run(
                ["which", "markitdown"],
                capture_output=True
            ).returncode == 0
        return _markitdown_available

    def can_handle(self, file_path: str) -> float:
        """
        Return confidence (0.0-1.0) based on file extension and complexity.
        """
        ext = Path(file_path).suffix.lower()

        # Not a PDF - use extension-based confidence
        if ext != '.pdf':
            common_formats = {
                '.md', '.txt', '.csv', '.json', '.xml', '.yaml', '.yml',
                '.html', '.htm', '.docx', '.xlsx', '.pptx',
                '.rtf', '.epub', '.ipynb'
            }
            if ext in common_formats:
                return 0.9
            return 0.0

        # PDF - use base class complexity detection -> _get_confidence()
        return super().can_handle(file_path)

    def _get_confidence(self, score: float) -> float:
        """Map complexity score to MarkItDown confidence."""
        return markitdown_confidence(score)

    def convert(self, input_path: str, output_path: str) -> ConversionResult:
        """Convert file using markitdown CLI."""
        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            return ConversionResult(
                success=False,
                engine=self.name,
                error=f"Input file not found: {input_path}"
            )

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            cmd = ["markitdown", str(input_file), "-o", str(output_file)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=MARKITDOWN_TIMEOUT
            )

            if result.returncode == 0:
                # Verify output file exists and has content
                if not output_file.exists():
                    return ConversionResult(
                        success=False,
                        engine=self.name,
                        error=f"Output file not created: {output_file}"
                    )
                if output_file.stat().st_size == 0:
                    return ConversionResult(
                        success=False,
                        engine=self.name,
                        error="Output file is empty (0 bytes)"
                    )
                return ConversionResult(
                    success=True,
                    output_path=str(output_file),
                    engine=self.name,
                    quality_score=80,  # Default score; actual quality varies by source format
                )
            else:
                return ConversionResult(
                    success=False,
                    engine=self.name,
                    error=result.stderr
                )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                engine=self.name,
                error=f"Conversion timeout ({MARKITDOWN_TIMEOUT}s)"
            )
        except FileNotFoundError:
            return ConversionResult(
                success=False,
                engine=self.name,
                error="markitdown not found. Run 'bash scripts/install_deps.sh'"
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                engine=self.name,
                error=str(e)
            )