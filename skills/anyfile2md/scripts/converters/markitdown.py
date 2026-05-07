# skills/anyfile2md/scripts/converters/markitdown.py
"""Markitdown converter implementation."""

import subprocess
from pathlib import Path

from .base import BaseConverter, ConversionResult
from .complexity import ComplexityDetector

MARKITDOWN_TIMEOUT = 60


class MarkitdownConverter(BaseConverter):
    """Converter using markitdown CLI."""

    @property
    def name(self) -> str:
        return "markitdown"

    @property
    def priority(self) -> int:
        """Markitdown has higher priority (lower number)."""
        return 10

    def is_available(self) -> bool:
        """Check if markitdown is installed."""
        return subprocess.run(
            ["which", "markitdown"],
            capture_output=True
        ).returncode == 0

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

        # PDF - use complexity detection
        try:
            detector = ComplexityDetector()
            result = detector.analyze(file_path)

            # Simple PDFs (score 0-3) - markitdown handles well
            if result.score <= 3:
                return 0.8
            # Medium complexity (score 4-7) - markitdown may struggle
            elif result.score <= 7:
                return 0.4
            # High complexity (score 8+) - markitdown not recommended
            else:
                return 0.2
        except Exception:
            # If complexity detection fails, assume simple
            return 0.5

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