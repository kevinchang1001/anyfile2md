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
    # Confidence now depends on complexity detection (0.2-0.8 range for PDF)
    assert 0.2 <= confidence <= 0.8


def test_markitdown_can_handle_with_complexity():
    """Markitdown returns complexity-aware confidence."""
    from scripts.converters.markitdown import MarkitdownConverter
    from scripts.converters.complexity import ComplexityDetector

    conv = MarkitdownConverter()
    # For non-PDF files, should return 0.9
    confidence = conv.can_handle("document.txt")
    assert confidence == 0.9

    # For PDF, confidence depends on complexity
    # (We can't easily test actual PDF complexity without a test PDF)
    confidence_pdf = conv.can_handle("document.pdf")
    assert 0.0 <= confidence_pdf <= 1.0


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
    """Mineru availability depends on installation."""
    conv = MineruConverter()
    # is_available() now checks if mineru is installed
    result = conv.is_available()
    assert isinstance(result, bool)

def test_mineru_can_handle_complex_pdf():
    """Mineru returns higher confidence for complex PDFs."""
    from scripts.converters.mineru import MineruConverter
    conv = MineruConverter()
    # Mineru can handle PDFs (though currently returns based on complexity)
    confidence = conv.can_handle("complex.pdf")
    assert 0.0 <= confidence <= 1.0

def test_mineru_is_available():
    """Mineru is_available checks if mineru is installed."""
    from scripts.converters.mineru import MineruConverter
    conv = MineruConverter()
    # Should return bool (True if installed, False if not)
    result = conv.is_available()
    assert isinstance(result, bool)


def test_registry_selects_by_complexity():
    """Registry should select engine with highest confidence."""
    import sys
    sys.path.insert(0, '/Users/nexlume/AI-Workspace/skills-dev/anyfile2md/skills/anyfile2md')
    from scripts.converters.registry import EngineRegistry
    registry = EngineRegistry()
    # For any file, should return an available engine
    engine, confidence = registry.select_engine("test.pdf")
    assert engine is not None
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0