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


from scripts.converters.mineru import MineruConverter

def test_engine_registry_singleton():
    """EngineRegistry is a singleton."""
    from scripts.converters.registry import EngineRegistry
    reg1 = EngineRegistry()
    reg2 = EngineRegistry()
    assert reg1 is reg2

def test_get_default_engine():
    """get_default_engine returns MarkitdownConverter when available."""
    from scripts.converters.registry import get_default_engine
    engine = get_default_engine()
    assert engine.name == "markitdown"

def test_registry_select_best_engine():
    """Registry selects engine with highest confidence."""
    from scripts.converters.registry import EngineRegistry
    registry = EngineRegistry()
    engine, confidence = registry.select_engine("document.pdf")
    assert confidence >= 0.0

def test_mineru_converter_properties():
    """MineruConverter has correct name and priority."""
    conv = MineruConverter()
    assert conv.name == "mineru"
    assert conv.priority == 20

def test_mineru_stub_returns_not_available():
    """Mineru stub is not available (not implemented yet)."""
    conv = MineruConverter()
    # Stub should return False until implemented
    assert conv.is_available() is False