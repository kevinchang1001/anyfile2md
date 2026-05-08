"""Unit tests for ComplexityDetector detection methods.

These tests verify the correctness of each detection method:
- _detect_headers_footers()
- _detect_scanned()
- _detect_multi_column()
- _detect_tables()
- _detect_language_ratio()

Run with: python -m pytest evals/test_complexity.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from scripts.converters.complexity import ComplexityDetector, ComplexityResult


class TestComplexityDetectorInit:
    """Test ComplexityDetector initialization."""

    def test_complexity_detector_initialization(self):
        """ComplexityDetector can be instantiated."""
        detector = ComplexityDetector()
        assert detector is not None

    def test_fitz_available_flag(self):
        """Detector sets fitz_available based on import."""
        detector = ComplexityDetector()
        assert hasattr(detector, 'fitz_available')


class TestQuickCheck:
    """Test quick_check() returns expected structure."""

    def test_quick_check_returns_dict(self):
        """quick_check returns expected structure."""
        detector = ComplexityDetector()
        result = detector.quick_check("skills/anyfile2md/examples/sample.md")
        assert isinstance(result, dict)
        assert "page_count" in result
        assert "has_headers_footers" in result
        assert "is_scanned" in result
        assert "has_tables" in result
        assert "has_multi_column" in result
        assert "language_ratio" in result
        assert "file_exists" in result
        assert "is_pdf" in result

    def test_quick_check_non_pdf(self):
        """quick_check handles non-PDF files."""
        detector = ComplexityDetector()
        result = detector.quick_check("skills/anyfile2md/examples/sample.md")
        assert result["is_pdf"] is False
        assert result["page_count"] == 0

    def test_quick_check_nonexistent_file(self):
        """quick_check handles nonexistent files."""
        detector = ComplexityDetector()
        result = detector.quick_check("/nonexistent/file.pdf")
        assert result["file_exists"] is False


class TestDetectHeadersFooters:
    """Test _detect_headers_footers() detection method."""

    def test_detect_headers_footers_same_text(self):
        """Detects headers when same text appears on multiple pages."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_text.return_value = "Header Text on every page"

        # doc[:3] calls __getitem__ with slice object
        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: mock_page if isinstance(i, int) else [mock_page, mock_page, mock_page])
        mock_doc.__len__ = Mock(return_value=3)

        assert detector._detect_headers_footers(mock_doc) is True

    def test_detect_headers_footers_different_text(self):
        """No headers when text differs between pages."""
        detector = ComplexityDetector()

        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 content"

        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 content"

        mock_page3 = Mock()
        mock_page3.get_text.return_value = "Page 3 content"

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page1, mock_page2, mock_page3][i])
        mock_doc.__len__ = Mock(return_value=3)

        assert detector._detect_headers_footers(mock_doc) is False

    def test_detect_headers_footers_few_pages(self):
        """Returns False for documents with fewer than 3 pages."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_text.return_value = "Some text"

        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=2)

        assert detector._detect_headers_footers(mock_doc) is False


class TestDetectScanned:
    """Test _detect_scanned() detection method."""

    def test_detect_scanned_with_images(self):
        """Detects scanned PDF when pages have images but little text."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_images.return_value = [Mock(), Mock()]  # 2 images
        mock_page.get_text.return_value = "   "  # Minimal whitespace

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page, mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page, mock_page]))
        mock_doc.__len__ = Mock(return_value=2)

        assert detector._detect_scanned(mock_doc) is True

    def test_detect_scanned_with_text(self):
        """Does not detect as scanned when pages have substantial text."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_images.return_value = [Mock()]  # Has image
        mock_page.get_text.return_value = "This is a substantial amount of text that exceeds fifty characters."

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page, mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page, mock_page]))
        mock_doc.__len__ = Mock(return_value=2)

        assert detector._detect_scanned(mock_doc) is False

    def test_detect_scanned_no_images(self):
        """Does not detect as scanned when no images present."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_images.return_value = []
        mock_page.get_text.return_value = "Normal text content"

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page, mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page, mock_page]))
        mock_doc.__len__ = Mock(return_value=2)

        assert detector._detect_scanned(mock_doc) is False


class TestDetectMultiColumn:
    """Test _detect_multi_column() detection method."""

    def test_detect_multi_column_true(self):
        """Detects multi-column when text appears at different x positions."""
        detector = ComplexityDetector()

        mock_page = Mock()
        # Need at least 3 blocks for the check to trigger, with 2+ distinct x positions
        mock_page.get_text = Mock(return_value={
            "blocks": [
                {"lines": [{"spans": [{"bbox": (50, 0, 200, 20)}]}]},
                {"lines": [{"spans": [{"bbox": (60, 10, 210, 30)}]}]},  # Same column (~0)
                {"lines": [{"spans": [{"bbox": (350, 0, 500, 20)}]}]}  # Different column (~3)
            ]
        })

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page, mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page, mock_page]))
        mock_doc.__len__ = Mock(return_value=2)

        assert detector._detect_multi_column(mock_doc) is True

    def test_detect_multi_column_false(self):
        """Does not detect multi-column when text is in single column."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_text = Mock(return_value={
            "blocks": [
                {"lines": [{"spans": [{"bbox": (100, 0, 300, 20)}]}]},
                {"lines": [{"spans": [{"bbox": (110, 10, 310, 30)}]}]},
                {"lines": [{"spans": [{"bbox": (105, 20, 305, 40)}]}]}
            ]
        })

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)

        assert detector._detect_multi_column(mock_doc) is False

    def test_detect_multi_column_few_blocks(self):
        """Does not detect multi-column with fewer than 3 blocks."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_text = Mock(return_value={
            "blocks": []
        })

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)

        assert detector._detect_multi_column(mock_doc) is False


class TestDetectTables:
    """Test _detect_tables() detection method."""

    def test_detect_tables_found(self):
        """Detects tables when table finder returns tables."""
        detector = ComplexityDetector()

        mock_table = Mock()
        mock_table.tables = [Mock(), Mock()]  # 2 tables found

        mock_page = Mock()
        mock_page.find_tables.return_value = mock_table

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page, mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page, mock_page]))
        mock_doc.__len__ = Mock(return_value=2)

        assert detector._detect_tables(mock_doc) is True

    def test_detect_tables_not_found(self):
        """Does not detect tables when none found."""
        detector = ComplexityDetector()

        mock_table = Mock()
        mock_table.tables = []

        mock_page = Mock()
        mock_page.find_tables.return_value = mock_table

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page, mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page, mock_page]))
        mock_doc.__len__ = Mock(return_value=2)

        assert detector._detect_tables(mock_doc) is False

    def test_detect_tables_exception(self):
        """Handles exceptions gracefully."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.find_tables.side_effect = Exception("PDF error")

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page])
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)

        assert detector._detect_tables(mock_doc) is False


class TestDetectLanguageRatio:
    """Test _detect_language_ratio() detection method."""

    def test_detect_language_ratio_chinese(self):
        """Detects high Chinese character ratio."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_text.return_value = "这是一段中文文本"

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page] * 5)
        mock_doc.__iter__ = Mock(return_value=iter([mock_page] * 5))
        mock_doc.__len__ = Mock(return_value=5)

        ratio = detector._detect_language_ratio(mock_doc)
        assert ratio > 0.7  # Should be mostly Chinese

    def test_detect_language_ratio_english(self):
        """Detects low Chinese character ratio for English text."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_text.return_value = "This is English text content"

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page] * 5)
        mock_doc.__iter__ = Mock(return_value=iter([mock_page] * 5))
        mock_doc.__len__ = Mock(return_value=5)

        ratio = detector._detect_language_ratio(mock_doc)
        assert ratio < 0.3  # Should be mostly non-Chinese

    def test_detect_language_ratio_empty(self):
        """Handles empty documents gracefully."""
        detector = ComplexityDetector()

        mock_page = Mock()
        mock_page.get_text.return_value = ""

        mock_doc = MagicMock()
        mock_doc.__getitem__ = Mock(side_effect=lambda i: [mock_page] * 5)
        mock_doc.__iter__ = Mock(return_value=iter([mock_page] * 5))
        mock_doc.__len__ = Mock(return_value=5)

        ratio = detector._detect_language_ratio(mock_doc)
        assert ratio == 1.0  # Default to all Chinese if no text


class TestAnalyze:
    """Test full analyze() method with weighted scoring."""

    def test_analyze_returns_complexity_result(self):
        """analyze() returns ComplexityResult with all fields."""
        detector = ComplexityDetector()
        result = detector.analyze("skills/anyfile2md/examples/sample.md")

        assert isinstance(result, ComplexityResult)
        assert hasattr(result, 'score')
        assert hasattr(result, 'factors')
        assert hasattr(result, 'recommended_engine')
        assert hasattr(result, 'is_scanned')
        assert hasattr(result, 'page_count')
        assert hasattr(result, 'has_headers_footers')
        assert hasattr(result, 'has_tables')
        assert hasattr(result, 'has_multi_column')

    def test_analyze_recommended_engine_markitdown(self):
        """Low complexity recommends markitdown."""
        detector = ComplexityDetector()

        with patch.object(detector, 'quick_check') as mock_quick:
            mock_quick.return_value = {
                "page_count": 5,
                "has_headers_footers": False,
                "is_scanned": False,
                "has_tables": False,
                "has_multi_column": False,
                "language_ratio": 1.0,
            }

            result = detector.analyze("/fake/path.pdf")

            assert result.recommended_engine == "markitdown"
            assert result.score < 4

    def test_analyze_recommended_engine_mineru(self):
        """High complexity recommends mineru."""
        detector = ComplexityDetector()

        with patch.object(detector, 'quick_check') as mock_quick:
            mock_quick.return_value = {
                "page_count": 50,  # >10: +1
                "has_headers_footers": True,  # +2
                "is_scanned": True,  # +5
                "has_tables": True,  # +3
                "has_multi_column": True,  # +3
                "language_ratio": 0.5,  # <0.7: +1
                # Total: 1+2+5+3+3+1 = 15 >= 8
            }

            result = detector.analyze("/fake/path.pdf")

            assert result.recommended_engine == "mineru"
            assert result.score >= 8

    def test_analyze_recommended_engine_prompt(self):
        """Medium complexity recommends user prompt."""
        detector = ComplexityDetector()

        with patch.object(detector, 'quick_check') as mock_quick:
            mock_quick.return_value = {
                "page_count": 20,  # +1
                "has_headers_footers": True,  # +2
                "is_scanned": False,
                "has_tables": True,  # +3
                "has_multi_column": False,
                "language_ratio": 1.0,
                # Total: 1+2+3 = 6 (between 4 and 7)
            }

            result = detector.analyze("/fake/path.pdf")

            assert result.recommended_engine == "prompt"
            assert 4 <= result.score < 8

    def test_analyze_factors_dict_populated(self):
        """factors dict is populated based on detected features."""
        detector = ComplexityDetector()

        with patch.object(detector, 'quick_check') as mock_quick:
            mock_quick.return_value = {
                "page_count": 50,
                "has_headers_footers": True,
                "is_scanned": False,
                "has_tables": True,
                "has_multi_column": True,
                "language_ratio": 0.5,
            }

            result = detector.analyze("/fake/path.pdf")

            assert "page_count" in result.factors
            assert "headers_footers" in result.factors
            assert "tables" in result.factors
            assert "multi_column" in result.factors
            assert "non_chinese" in result.factors


class TestComplexityScoringBoundaries:
    """Test scoring at exact boundary values."""

    def test_score_0_to_3_markitdown(self):
        """Score 0-3 should recommend markitdown."""
        detector = ComplexityDetector()

        with patch.object(detector, 'quick_check') as mock_quick:
            mock_quick.return_value = {
                "page_count": 5,
                "has_headers_footers": False,
                "is_scanned": False,
                "has_tables": False,
                "has_multi_column": False,
                "language_ratio": 1.0,
            }
            result = detector.analyze("/fake/path.pdf")
            assert result.recommended_engine == "markitdown"

    def test_score_4_to_7_prompt(self):
        """Score 4-7 should recommend prompt."""
        detector = ComplexityDetector()

        with patch.object(detector, 'quick_check') as mock_quick:
            mock_quick.return_value = {
                "page_count": 20,  # +1
                "has_headers_footers": True,  # +2
                "is_scanned": False,
                "has_tables": True,  # +3
                "has_multi_column": False,
                "language_ratio": 1.0,
                # Total: 1+2+3 = 6
            }
            result = detector.analyze("/fake/path.pdf")
            assert result.recommended_engine == "prompt"

    def test_score_8_plus_mineru(self):
        """Score 8+ should recommend mineru."""
        detector = ComplexityDetector()

        with patch.object(detector, 'quick_check') as mock_quick:
            mock_quick.return_value = {
                "page_count": 20,  # +1
                "has_headers_footers": True,  # +2
                "is_scanned": True,  # +5
                "has_tables": False,
                "has_multi_column": False,
                "language_ratio": 1.0,
                # Total: 1+2+5 = 8
            }
            result = detector.analyze("/fake/path.pdf")
            assert result.recommended_engine == "mineru"
