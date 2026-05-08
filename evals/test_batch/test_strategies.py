import pytest
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, "scripts")
from batch.strategies import ConcurrencyStrategy, EngineAwareStrategy, FixedConcurrencyStrategy


def test_fixed_concurrency_strategy():
    strategy = FixedConcurrencyStrategy(max_workers=4)
    assert strategy.get_max_workers("any_file.pdf") == 4


def test_engine_aware_strategy_init():
    strategy = EngineAwareStrategy(cpu_concurrency=4)
    assert strategy.cpu_concurrency == 4


def test_engine_aware_strategy_gpu_sequential():
    """GPU 引擎应该返回 1（串行）。"""
    strategy = EngineAwareStrategy(cpu_concurrency=4)
    mock_engine = MagicMock()
    mock_engine.name = "mineru"
    with patch("batch.strategies.select_best_engine", return_value=(mock_engine, 0.8)):
        assert strategy.get_max_workers("test.pdf") == 1


def test_engine_aware_strategy_cpu_parallel():
    """CPU 引擎应该返回配置的并发数。"""
    strategy = EngineAwareStrategy(cpu_concurrency=4)
    mock_engine = MagicMock()
    mock_engine.name = "markitdown"
    with patch("batch.strategies.select_best_engine", return_value=(mock_engine, 0.8)):
        assert strategy.get_max_workers("test.pdf") == 4