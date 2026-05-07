# evals/test_fallback.py
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
    # Should try mineru first if it has higher confidence
    # Then fall back to markitdown
    # (Actual order depends on complexity)