# scripts/batch/strategies.py
"""并发策略。"""

from abc import ABC, abstractmethod

# Import from the converters registry
import sys
sys.path.insert(0, "skills/anyfile2md/scripts")
from converters.registry import select_best_engine


class ConcurrencyStrategy(ABC):
    """并发策略基类。"""

    @abstractmethod
    def get_max_workers(self, file_path: str) -> int:
        """返回给定文件的最大工作数。"""
        pass


class EngineAwareStrategy(ConcurrencyStrategy):
    """引擎感知并发策略。

    根据文件类型和引擎返回最大并发数。
    - GPU 引擎 (MinerU): 串行 (1)
    - CPU 引擎 (MarkItDown): 并行 (可配置)
    """

    def __init__(self, cpu_concurrency: int = 4):
        self.cpu_concurrency = cpu_concurrency

    def get_max_workers(self, file_path: str) -> int:
        """根据引擎类型返回最大并发数。"""
        engine, confidence = select_best_engine(file_path)
        if engine and engine.name == "mineru":
            return 1
        return self.cpu_concurrency


class FixedConcurrencyStrategy(ConcurrencyStrategy):
    """固定并发数策略。"""

    def __init__(self, max_workers: int):
        self.max_workers = max_workers

    def get_max_workers(self, file_path: str) -> int:
        return self.max_workers