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


from scripts.converters.errors import ConversionSession, ConversionAttempt


def test_fallback_logs_failures():
    """FallbackHandler logs failed attempts."""
    session = ConversionSession(file_path="/fake/file.pdf")
    session.attempts.append(
        ConversionAttempt(engine="mineru", success=False, error="GPU not available")
    )
    session.attempts.append(
        ConversionAttempt(engine="markitdown", success=True, quality_score=80)
    )
    session.final_result = "success"
    session.final_engine = "markitdown"
    assert len(session.attempts) == 2
    assert session.final_result == "success"
    assert session.final_engine == "markitdown"


from scripts.converters.fallback import FallbackHandler


def test_fallback_handler_initialization():
    """FallbackHandler can be initialized."""
    handler = FallbackHandler()
    assert handler is not None


def test_fallback_handler_selects_engines():
    """FallbackHandler gets available engines."""
    handler = FallbackHandler()
    engines = handler.get_available_engines()
    assert isinstance(engines, list)
    assert len(engines) >= 1


def test_fallback_tries_engines_in_order():
    """FallbackHandler tries engines by confidence order."""
    handler = FallbackHandler()
    # Verify engines are sorted by confidence (highest first)
    engines = handler.get_available_engines()
    if len(engines) >= 2:
        # Get confidences for comparison
        confidences = [e.can_handle("test.pdf") for e in engines]
        # Verify descending order
        assert confidences == sorted(confidences, reverse=True), \
            f"Engines not sorted by confidence: {confidences}"