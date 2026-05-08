"""Tests for confidence module."""

from scripts.converters.confidence import (
    markitdown_confidence,
    mineru_confidence,
    get_confidence,
    ConfidenceThreshold,
    MARKITDOWN_CONFIDENCE,
    MINERU_CONFIDENCE,
)


def test_markitdown_confidence_simple():
    """MarkItDown confidence for simple PDFs (score 0-3)."""
    assert markitdown_confidence(0) == 0.8
    assert markitdown_confidence(1) == 0.8
    assert markitdown_confidence(3) == 0.8


def test_markitdown_confidence_medium():
    """MarkItDown confidence for medium PDFs (score 4-7)."""
    assert markitdown_confidence(4) == 0.4
    assert markitdown_confidence(5) == 0.4
    assert markitdown_confidence(7) == 0.4


def test_markitdown_confidence_complex():
    """MarkItDown confidence for complex PDFs (score 8+)."""
    assert markitdown_confidence(8) == 0.2
    assert markitdown_confidence(9) == 0.2
    assert markitdown_confidence(10) == 0.2


def test_mineru_confidence_simple():
    """MinerU confidence for simple PDFs (score 0-3)."""
    assert mineru_confidence(0) == 0.3
    assert mineru_confidence(1) == 0.3
    assert mineru_confidence(3) == 0.3


def test_mineru_confidence_medium():
    """MinerU confidence for medium PDFs (score 4-7)."""
    assert mineru_confidence(4) == 0.5
    assert mineru_confidence(5) == 0.5
    assert mineru_confidence(7) == 0.5


def test_mineru_confidence_complex():
    """MinerU confidence for complex PDFs (score 8+)."""
    assert mineru_confidence(8) == 0.9
    assert mineru_confidence(9) == 0.9
    assert mineru_confidence(10) == 0.9


def test_confidence_thresholds_are_complementary():
    """MarkItDown and MinerU confidences are complementary across complexity range."""
    for score in range(11):
        markitdown = markitdown_confidence(score)
        mineru = mineru_confidence(score)
        # Higher complexity should favor MinerU
        if score >= 8:
            assert mineru > markitdown, f"Score {score}: mineru={mineru} should be > markitdown={markitdown}"
        # Lower complexity should favor MarkItDown
        elif score <= 3:
            assert markitdown > mineru, f"Score {score}: markitdown={markitdown} should be > mineru={mineru}"


def test_confidence_threshold_dataclass():
    """ConfidenceThreshold is a valid dataclass."""
    threshold = ConfidenceThreshold(max_score=5.0, confidence=0.7)
    assert threshold.max_score == 5.0
    assert threshold.confidence == 0.7


def test_markitdown_confidence_at_boundaries():
    """Test MarkItDown at boundary values (3, 7, 8)."""
    # At exact thresholds
    assert markitdown_confidence(3) == 0.8   # Score 3 is simple
    assert markitdown_confidence(4) == 0.4   # Score 4 is medium
    assert markitdown_confidence(7) == 0.4   # Score 7 is medium
    assert markitdown_confidence(8) == 0.2   # Score 8 is complex


def test_mineru_confidence_at_boundaries():
    """Test MinerU at boundary values (3, 7, 8)."""
    assert mineru_confidence(3) == 0.3   # Score 3 is simple
    assert mineru_confidence(4) == 0.5   # Score 4 is medium
    assert mineru_confidence(7) == 0.5   # Score 7 is medium
    assert mineru_confidence(8) == 0.9   # Score 8 is complex