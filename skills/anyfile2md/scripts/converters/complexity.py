# skills/anyfile2md/scripts/converters/complexity.py
"""Complexity detection for PDF files using weighted scoring model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


@dataclass
class ComplexityResult:
    """Result of complexity analysis."""
    score: int
    factors: dict
    recommended_engine: str  # "markitdown", "mineru", or "prompt"
    is_scanned: bool = False
    page_count: int = 0
    has_headers_footers: bool = False
    has_tables: bool = False
    has_multi_column: bool = False


class ComplexityDetector:
    """
    Detects PDF complexity using weighted scoring model.

    Scoring:
    - Page count > 10: +1
    - Headers/footers detected: +2
    - Multi-column layout: +3
    - Cross-page tables: +3
    - Non-Chinese ratio > 30%: +1
    - Scanned/image-based: +5

    Threshold:
    - 0-3: markitdown (fast)
    - 4-7: User prompt
    - 8+: mineru (high quality)
    """

    def __init__(self):
        self.fitz_available = fitz is not None

    def quick_check(self, file_path: str) -> dict:
        """
        Quick pre-check without full conversion.
        Returns dict with detected features.
        """
        result = {
            "page_count": 0,
            "has_headers_footers": False,
            "is_scanned": False,
            "has_tables": False,
            "has_multi_column": False,
            "language_ratio": 1.0,  # Chinese ratio
            "file_exists": Path(file_path).exists(),
            "is_pdf": Path(file_path).suffix.lower() == ".pdf",
        }

        if not result["is_pdf"]:
            return result

        if not self.fitz_available:
            return result

        try:
            with fitz.open(file_path) as doc:
                result["page_count"] = len(doc)

                # Check first few pages for headers/footers
                result["has_headers_footers"] = self._detect_headers_footers(doc)

                # Check for scanned (image-based) pages
                result["is_scanned"] = self._detect_scanned(doc)

                # Check for multi-column layout
                result["has_multi_column"] = self._detect_multi_column(doc)

                # Check for tables
                result["has_tables"] = self._detect_tables(doc)

                # Language ratio check
                result["language_ratio"] = self._detect_language_ratio(doc)
        except Exception:
            pass

        return result

    def analyze(self, file_path: str) -> ComplexityResult:
        """
        Full complexity analysis with weighted scoring.
        """
        quick = self.quick_check(file_path)
        score = 0
        factors = {}

        # Page count > 10: +1
        if quick["page_count"] > 10:
            score += 1
            factors["page_count"] = quick["page_count"]

        # Headers/footers: +2
        if quick["has_headers_footers"]:
            score += 2
            factors["headers_footers"] = True

        # Multi-column layout: +3
        if quick["has_multi_column"]:
            score += 3
            factors["multi_column"] = True

        # Cross-page tables: +3
        if quick["has_tables"]:
            score += 3
            factors["tables"] = True

        # Non-Chinese ratio > 30%: +1
        if quick["language_ratio"] < 0.7:
            score += 1
            factors["non_chinese"] = True

        # Scanned: +5
        if quick["is_scanned"]:
            score += 5
            factors["scanned"] = True

        # Determine recommended engine
        if score >= 8:
            engine = "mineru"
        elif score >= 4:
            engine = "prompt"  # User should choose
        else:
            engine = "markitdown"

        return ComplexityResult(
            score=score,
            factors=factors,
            recommended_engine=engine,
            is_scanned=quick["is_scanned"],
            page_count=quick["page_count"],
            has_headers_footers=quick["has_headers_footers"],
            has_tables=quick["has_tables"],
            has_multi_column=quick["has_multi_column"],
        )

    def _detect_headers_footers(self, doc) -> bool:
        """Detect headers/footers in first 3 pages."""
        if len(doc) < 3:
            return False

        texts = []
        for page in doc[:3]:
            text = page.get_text().strip()
            if text:
                texts.append(text[:100])  # First 100 chars

        # If same text appears on multiple pages
        if len(set(texts)) < len(texts):
            return True
        return False

    def _detect_scanned(self, doc) -> bool:
        """Detect if PDF is scanned (image-based)."""
        for page in doc[:3]:  # Check first 3 pages
            images = page.get_images()
            if len(images) > 0:
                # Check if page has minimal text
                text = page.get_text().strip()
                if len(text) < 50:
                    return True
        return False

    def _detect_multi_column(self, doc) -> bool:
        """Detect multi-column layout by analyzing text block positions.

        Optimized: uses "blocks" instead of "dict" and samples only page 0.
        """
        if len(doc) == 0:
            return False

        # Only check first page for speed (first page is usually representative)
        page = doc[0]
        try:
            blocks = page.get_text("blocks")
        except Exception:
            return False

        if len(blocks) < 3:
            return False

        # Get x coordinates of text blocks
        x_coords = []
        for block in blocks:
            if isinstance(block, (list, tuple)) and len(block) >= 4:
                x0 = block[0]
                x_coords.append(x0)

        if len(x_coords) < 3:
            return False

        # Check for distinct column positions
        # If text appears in significantly different x positions, likely multi-column
        x_set = set()
        for x in x_coords:
            # Group by ~100px buckets
            x_set.add(int(x / 100))

        return len(x_set) >= 2

    def _detect_tables(self, doc) -> bool:
        """Detect tables by looking for structured grid patterns."""
        for page in doc[:3]:  # Check first 3 pages
            try:
                table = page.find_tables()
                # PyMuPDF returns a TableFinder object with .tables attribute
                if hasattr(table, 'tables') and len(table.tables) > 0:
                    return True
            except Exception:
                pass
        return False

    def _detect_language_ratio(self, doc) -> float:
        """Estimate Chinese character ratio."""
        import re
        chinese_chars = 0
        total_chars = 0

        for page in doc[:5]:  # Sample first 5 pages
            text = page.get_text()
            for char in text:
                if re.search(r'[一-鿿]', char):  # Chinese
                    chinese_chars += 1
                if char.strip():
                    total_chars += 1

        if total_chars == 0:
            return 1.0
        return chinese_chars / total_chars


# Module-level lazy singleton for ComplexityDetector
_detector: Optional[ComplexityDetector] = None


def get_detector() -> ComplexityDetector:
    """
    Get the global ComplexityDetector instance.

    Uses lazy initialization - the detector is only created when first accessed.
    This avoids importing PyMuPDF until actually needed.
    """
    global _detector
    if _detector is None:
        _detector = ComplexityDetector()
    return _detector