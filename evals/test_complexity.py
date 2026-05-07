import pytest
from scripts.converters.complexity import ComplexityDetector

def test_complexity_detector_initialization():
    """ComplexityDetector can be instantiated."""
    detector = ComplexityDetector()
    assert detector is not None

def test_quick_check_returns_dict():
    """quick_check returns expected structure."""
    detector = ComplexityDetector()
    result = detector.quick_check("skills/anyfile2md/examples/sample.md")
    assert isinstance(result, dict)
    assert "page_count" in result
    assert "has_headers_footers" in result
    assert "is_scanned" in result
    assert "has_tables" in result
    assert "has_multi_column" in result