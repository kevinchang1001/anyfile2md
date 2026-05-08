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


def test_mineru_convert_uses_do_parse():
    """MineruConverter uses do_parse API for conversion."""
    from unittest.mock import patch, MagicMock
    from scripts.converters.mineru import MineruConverter

    conv = MineruConverter()

    # Mock do_parse to prevent actual API call
    with patch('mineru.cli.common.do_parse') as mock_do_parse:
        mock_do_parse.return_value = None

        # Create a temp PDF file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            pdf_path = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = f"{tmpdir}/output.md"

            # Mock read_fn to return bytes
            with patch('mineru.cli.common.read_fn', return_value=b'%PDF-1.4 test content'):
                result = conv.convert(pdf_path, output_path)

            # Verify do_parse was called
            assert mock_do_parse.called

    import os
    os.unlink(pdf_path)