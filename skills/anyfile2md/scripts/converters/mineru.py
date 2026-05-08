"""MinerU converter implementation."""

import subprocess
from pathlib import Path

from .base import BaseConverter, ConversionResult
from .confidence import mineru_confidence

# Module-level cache for availability check
_mineru_available = None


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

    def __init__(self, detector=None):
        super().__init__(detector)

    def is_available(self) -> bool:
        """
        Check if MinerU is installed and API functions are available (cached).
        """
        global _mineru_available
        if _mineru_available is None:
            try:
                from mineru.cli.common import do_parse, read_fn
                _mineru_available = True
            except ImportError:
                _mineru_available = False
        return _mineru_available

    def can_handle(self, file_path: str) -> float:
        """
        MinerU excels at complex PDFs.
        Returns confidence based on complexity score.
        """
        ext = Path(file_path).suffix.lower()
        if ext != '.pdf':
            return 0.0

        # Use base class complexity detection -> _get_confidence()
        return super().can_handle(file_path)

    def _get_confidence(self, score: float) -> float:
        """Map complexity score to MinerU confidence."""
        return mineru_confidence(score)

    def convert(self, input_path: str, output_path: str) -> ConversionResult:
        """Convert file using MinerU do_parse API."""
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

            # Import MinerU functions
            from mineru.cli.common import do_parse, read_fn

            # Read PDF bytes
            pdf_bytes = read_fn(input_file)

            # Determine backend based on GPU availability
            backend = self._detect_backend()

            # Language hint (Chinese document by default for电力行业)
            lang = self._detect_language(input_path)

            # Create temp output directory (MinerU writes to {output_dir}/{name}/auto/)
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_output:
                # Call MinerU API
                do_parse(
                    output_dir=tmp_output,
                    pdf_file_names=[input_file.stem],
                    pdf_bytes_list=[pdf_bytes],
                    p_lang_list=[lang],
                    backend=backend,
                    parse_method="auto",
                    formula_enable=True,
                    table_enable=True,
                    f_dump_md=True,
                    f_dump_content_list=False,
                    f_dump_middle_json=False,
                    f_dump_model_output=False,
                    f_dump_orig_pdf=False,
                )

                # Read generated markdown
                # Try both "auto" (pipeline) and "hybrid_auto" (hybrid-auto-engine) paths
                stem_dir = Path(tmp_output) / input_file.stem
                md_path = None
                for subdir in ["auto", "hybrid_auto"]:
                    candidate = stem_dir / subdir / f"{input_file.stem}.md"
                    if candidate.exists():
                        md_path = candidate
                        break

                if md_path and md_path.exists():
                    md_content = md_path.read_text(encoding='utf-8')
                    # Verify content is not empty
                    if len(md_content.strip()) == 0:
                        return ConversionResult(
                            success=False,
                            engine=self.name,
                            error=f"MinerU output is empty: {md_path}"
                        )
                    # Write to final output
                    output_file.write_text(md_content, encoding='utf-8')

                    return ConversionResult(
                        success=True,
                        output_path=str(output_file),
                        engine=self.name,
                        quality_score=90
                    )
                else:
                    return ConversionResult(
                        success=False,
                        engine=self.name,
                        error=f"MinerU output not found. Tried: auto, hybrid_auto in {stem_dir}"
                    )

        except Exception as e:
            return ConversionResult(
                success=False,
                engine=self.name,
                error=str(e)
            )

    def _detect_backend(self) -> str:
        """Detect GPU availability and return appropriate backend."""
        # Check for NVIDIA GPU
        try:
            result = subprocess.run(
                ["nvidia-smi", "-L"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return "hybrid-auto-engine"  # NVIDIA GPU available
        except Exception:
            pass

        # Check for Apple Silicon MPS (mlx_vlm is installed)
        try:
            import torch
            if torch.backends.mps.is_available():
                return "hybrid-auto-engine"  # Apple Silicon MPS available
        except Exception:
            pass

        return "pipeline"  # CPU fallback

    def _detect_language(self, file_path: str) -> str:
        """Detect document language based on file path hints."""
        # Default to Chinese for电力行业 documents
        return "ch"
