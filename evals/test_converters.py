import pytest
from scripts.converters.base import BaseConverter, ConversionResult

def test_base_converter_is_abstract():
    """BaseConverter cannot be instantiated directly"""
    with pytest.raises(TypeError):
        BaseConverter()

def test_conversion_result_structure():
    """ConversionResult has required fields"""
    result = ConversionResult(
        success=True,
        output_path="/tmp/out.md",
        engine="test",
        quality_score=100
    )
    assert result.success is True
    assert result.output_path == "/tmp/out.md"
    assert result.engine == "test"
    assert result.quality_score == 100


from scripts.converters.markitdown import MarkitdownConverter

def test_markitdown_converter_properties():
    """MarkitdownConverter has correct name and priority."""
    conv = MarkitdownConverter()
    assert conv.name == "markitdown"
    assert conv.priority == 10

def test_markitdown_can_handle_pdf():
    """Markitdown can handle PDF files."""
    conv = MarkitdownConverter()
    confidence = conv.can_handle("document.pdf")
    assert confidence == 0.7