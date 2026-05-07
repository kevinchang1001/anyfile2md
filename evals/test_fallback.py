# evals/test_fallback.py
from scripts.converters.errors import ConversionError, ErrorTemplate


def test_conversion_error_structure():
    """ConversionError has required fields."""
    error = ConversionError(
        engine="mineru",
        reason="GPU not available",
        solutions=["Install GPU drivers", "Use CPU mode"]
    )
    assert error.engine == "mineru"
    assert error.reason == "GPU not available"
    assert len(error.solutions) == 2


def test_conversion_error_str():
    """ConversionError formats nicely."""
    error = ConversionError(
        engine="mineru",
        reason="GPU not available",
        solutions=["Install GPU drivers"]
    )
    error_str = str(error)
    assert "mineru" in error_str
    assert "GPU not available" in error_str
    assert "Install GPU drivers" in error_str


def test_error_template_for_engine():
    """ErrorTemplate provides solutions for common errors."""
    template = ErrorTemplate.for_engine("markitdown")
    assert "markitdown" in template
    assert "install" in template.lower() or "pip" in template.lower()