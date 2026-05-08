# scripts/batch/result.py
"""批量转换结果数据类。"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FileConversionRecord:
    """单个文件的转换记录。"""

    input_path: str
    output_path: str
    engine: str
    quality_score: int
    duration_seconds: float
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class BatchResult:
    """批量处理结果。"""

    total: int
    succeeded: int
    failed: int
    skipped: int
    duration_seconds: float
    success_details: list[FileConversionRecord] = field(default_factory=list)
    failure_details: list[FileConversionRecord] = field(default_factory=list)
    log_file: Optional[str] = None
    failed_list_file: Optional[str] = None


@dataclass
class RetryPolicy:
    """重试策略配置。"""

    max_retries: int = 1
    retry_delay: float = 1.0
    exponential_backoff: bool = False
    max_delay: float = 30.0
    jitter: bool = False

    @classmethod
    def default(cls) -> "RetryPolicy":
        return cls(max_retries=1, retry_delay=1.0)

    def get_retry_delay(self, attempt: int) -> float:
        """计算第 attempt 次重试的延迟。"""
        delay = self.retry_delay
        if self.exponential_backoff:
            delay = min(delay * (2 ** attempt), self.max_delay)
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        return delay


@dataclass
class QueuedFile:
    """队列中的文件。"""

    input_path: str
    output_path: str
    relative_path: str