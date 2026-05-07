"""MinerU converter implementation."""

import subprocess
from pathlib import Path

from .base import BaseConverter, ConversionResult
from .complexity import ComplexityDetector


class MineruConverter(BaseConverter):
    """
    Converter using MinerU for complex PDFs.

    MinerU excels at:
    - Multi-column layouts
    - Tables spanning pages
    - Headers/footers
    - Scanned documents
    """

    MINERU_TIMEOUT = 300  # 5 minutes

    @property
    def name(self) -> str:
        return "mineru"

    @property
    def priority(self) -> int:
        """MinerU has lower priority than markitdown."""
        return 20

    def is_available(self) -> bool:
        """
        Check if MinerU is installed and available.
        """
        try:
            result = subprocess.run(
                ["python", "-c", "import mineru"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def can_handle(self, file_path: str) -> float:
        """
        MinerU excels at complex PDFs.
        Returns confidence based on complexity score.
        """
        ext = Path(file_path).suffix.lower()
        if ext != '.pdf':
            return 0.0

        try:
            detector = ComplexityDetector()
            result = detector.analyze(file_path)

            # High complexity (score 8+) - MinerU recommended
            if result.score >= 8:
                return 0.9
            # Medium complexity (score 4-7) - MinerU viable
            elif result.score >= 4:
                return 0.5
            # Simple (score 0-3) - MinerU overkill
            else:
                return 0.3
        except Exception:
            return 0.0

    def convert(self, input_path: str, output_path: str) -> ConversionResult:
        """
        Convert file using MinerU.
        """
        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            return ConversionResult(
                success=False,
                engine=self.name,
                error=f"Input file not found: {input_path}"
            )

        if not self.is_available():
            return ConversionResult(
                success=False,
                engine=self.name,
                error="MinerU not available. Run: pip install mineru"
            )

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # MinerU Python API - simplified call
            cmd = [
                "python", "-c",
                f"from mineru import convert; convert('{input_file}', '{output_file}')"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.MINERU_TIMEOUT
            )

            if result.returncode == 0:
                return ConversionResult(
                    success=True,
                    output_path=str(output_file),
                    engine=self.name,
                    quality_score=90
                )
            else:
                # MinerU API may differ - provide helpful error
                error_msg = result.stderr if result.stderr else "Unknown error"
                return ConversionResult(
                    success=False,
                    engine=self.name,
                    error=f"MinerU API error: {error_msg}. Note: MinerU integration requires Phase 4 implementation."
                )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                engine=self.name,
                error=f"Conversion timeout ({self.MINERU_TIMEOUT}s)"
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                engine=self.name,
                error=str(e)
            )
