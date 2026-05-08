# evals/test_mineru_api.py
from scripts.converters.errors import MineruError

def test_mineru_error_structure():
    """MineruError has required fields for API errors."""
    error = MineruError(
        reason="GPU not available",
        solutions=["Install CUDA drivers", "Use CPU mode"]
    )
    assert error.reason == "GPU not available"
    assert len(error.solutions) == 2

def test_mineru_error_inherits_conversion_error():
    """MineruError inherits from ConversionError."""
    from scripts.converters.errors import ConversionError
    error = MineruError(reason="test", solutions=["fix"])
    assert isinstance(error, ConversionError)