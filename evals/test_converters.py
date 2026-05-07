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