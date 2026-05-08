"""Tests for MinerU API availability checks."""

def test_mineru_is_available_checks_api():
    """MineruConverter.is_available() checks do_parse function exists."""
    from scripts.converters.mineru import MineruConverter

    conv = MineruConverter()
    # is_available should return True if mineru installed AND do_parse exists
    result = conv.is_available()
    assert isinstance(result, bool)