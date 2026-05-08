# 批量转换系统设计规范

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可扩展的批量文档转换系统，支持大规模文件处理、目录递归扫描、引擎感知并发、详细进度报告和失败重试。

**Architecture:** 混合架构 - BatchProcessor 作为核心调度器，复用现有的 FallbackHandler 进行实际转换。职责分离：队列管理、并发控制、进度报告由 BatchProcessor 负责，引擎选择和转换由 FallbackHandler 负责。

**Tech Stack:** Python, tqdm (进度条), concurrent.futures (并发控制)

---

## 1. 概述

### 1.1 解决的问题

当前系统 (`convert.py`) 支持单文件转换和简单的批量模式，但存在以下局限：

- 批量模式无并发控制，大文件处理时资源利用率低
- 无重试机制，临时性失败导致整个批次中断
- 进度报告简单，无法满足自动化脚本需求
- 无灵活的文件发现机制（递归、通配符）

### 1.2 设计目标

| 目标 | 描述 |
|------|------|
| 大规模处理 | 支持 1000+ 文件的批量转换 |
| 引擎感知并发 | GPU 引擎串行，CPU 引擎可并行 |
| 灵活输入 | 支持文件列表、目录递归、通配符 |
| 详细报告 | 进度条、详细日志、失败清单 |
| 失败恢复 | 重试机制 + 失败跳过 |

---

## 2. 系统架构

### 2.1 组件图

```
┌─────────────────────────────────────────────────────────────┐
│                        BatchProcessor                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  FileQueue  │  │Concurrency  │  │    ProgressReporter │ │
│  │   队列管理   │  │   策略      │  │      进度报告       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      FallbackHandler                        │
│                   (复用现有转换逻辑)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      EngineRegistry                         │
│            MarkItDown  │  MinerU (GPU/CPU)                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心类

| 类 | 文件 | 职责 |
|----|------|------|
| `BatchProcessor` | `processor.py` | 批量处理调度器 |
| `BatchResult` | `result.py` | 结果数据类 |
| `FileQueue` | `queue.py` | 文件队列管理 |
| `ConcurrencyStrategy` | `strategies.py` | 并发策略基类 |
| `EngineAwareStrategy` | `strategies.py` | 引擎感知并发策略 |
| `ProgressReporter` | `reporter.py` | 进度报告器 |

---

## 3. 详细设计

### 3.1 BatchProcessor

**位置:** `scripts/batch/processor.py`

```python
class BatchProcessor:
    def __init__(
        self,
        concurrency: Optional[int] = None,
        retry_policy: RetryPolicy = None,
        progress_mode: str = "detailed",
        output_mode: str = "preserve",
    ):
        """
        初始化批量处理器。

        Args:
            concurrency: 并发数，None 表示引擎感知模式
            retry_policy: 重试策略配置
            progress_mode: 进度模式 ("silent", "simple", "detailed")
            output_mode: 输出模式 ("flat", "preserve", "by_type")
        """

    def process_batch(
        self,
        input_sources: list[str],
        output_dir: str,
        patterns: list[str] = None,
        overwrite: bool = False,
    ) -> BatchResult:
        """
        执行批量转换。

        Args:
            input_sources: 输入源列表（文件/目录/通配符）
            output_dir: 输出目录
            patterns: 文件过滤模式（如 ["*.pdf", "*.docx"]）
            overwrite: 是否覆盖已存在的文件

        Returns:
            BatchResult: 包含统计、日志、失败列表
        """
```

### 3.2 BatchResult

**位置:** `scripts/batch/result.py`

```python
@dataclass
class BatchResult:
    """批量处理结果。"""

    total: int
    succeeded: int
    failed: int
    skipped: int
    duration_seconds: float

    success_details: list[FileConversionRecord]  # 成功详情
    failure_details: list[FileConversionRecord]  # 失败详情（含错误信息）

    log_file: Optional[str]  # 详细日志路径
    failed_list_file: Optional[str]  # 失败清单路径


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
class RetryPolicy:
    """重试策略配置。"""

    max_retries: int = 1
    retry_delay: float = 1.0  # 秒
    exponential_backoff: bool = False
    max_delay: float = 30.0  # 最大延迟秒数
    jitter: bool = False  # 添加随机抖动

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
            delay = delay * (0.5 + random.random())  # 0.5-1.5 倍
        return delay


@dataclass
class QueuedFile:
    """队列中的文件。"""

    input_path: str
    output_path: str
    relative_path: str  # 相对于输出目录的路径（用于保持结构）


**位置:** `scripts/batch/queue.py`

```python
class FileQueue:
    """文件队列管理器。"""

    def __init__(self, patterns: list[str] = None):
        self.patterns = patterns or ["*.pdf", "*.docx", "*.pptx", "*.xlsx"]

    def build_from_sources(
        self,
        sources: list[str],
        output_dir: str,
        output_mode: str = "preserve",
    ) -> list[QueuedFile]:
        """
        从多种输入源构建文件队列。

        Args:
            sources: 输入源列表
            output_dir: 输出目录
            output_mode: 输出模式

        Returns:
            待处理文件列表
        """
```

**支持的输入源类型：**

| 类型 | 示例 | 行为 |
|------|------|------|
| 单文件 | `file.pdf` | 直接添加 |
| 文件列表 | `["a.pdf", "b.pdf"]` | 逐一添加 |
| 目录 | `dir/` | 递归扫描 |
| 通配符 | `*.pdf` | glob 匹配 |
| 混合 | `["dir/", "*.docx"]` | 全部支持 |

**输出模式：**

| 模式 | 行为 |
|------|------|
| `preserve` | 保持目录结构（默认） |
| `flat` | 全部输出到同一目录 |
| `by_type` | 按文件类型分组 |

### 3.4 并发策略

**位置:** `scripts/batch/strategies.py`

```python
from abc import ABC, abstractmethod
from registry import select_best_engine  # 复用现有的引擎选择函数


class ConcurrencyStrategy(ABC):
    """并发策略基类。"""

    @abstractmethod
    def get_max_workers(self, file_path: str) -> int:
        """返回给定文件的最大工作数。"""
        pass


class EngineAwareStrategy(ConcurrencyStrategy):
    """引擎感知并发策略。"""

    def get_max_workers(self, file_path: str) -> int:
        """
        根据文件类型和引擎返回最大并发数。

        - GPU 引擎 (MinerU): 串行 (1)
        - CPU 引擎 (MarkItDown): 并行 (可配置)
        """
        # 内部使用 EngineRegistry 判断
        engine, confidence = select_best_engine(file_path)
        if engine and engine.name == "mineru":
            return 1  # GPU 引擎串行
        return self.cpu_concurrency  # CPU 引擎可并行


class FixedConcurrencyStrategy(ConcurrencyStrategy):
    """固定并发数策略。"""

    def __init__(self, max_workers: int):
        self.max_workers = max_workers

    def get_max_workers(self, file_path: str) -> int:
        return self.max_workers
```

### 3.5 重试策略

**位置:** `scripts/batch/result.py` (RetryPolicy)

RetryPolicy 定义见 3.2 节。

**重试流程：**

```
转换失败（所有引擎已尝试）
    ↓
检查 RetryPolicy
    ↓
retry_count < max_retries?
    ├─ Yes → 等待 delay 秒 → 使用同一引擎重试
    └─ No  → 标记为失败，继续下一个
```

**重试语义说明：**
- BatchProcessor 的重试是**文件级别重试**，与 FallbackHandler 的**引擎轮换**是正交的
- FallbackHandler 会尝试所有可用引擎，只有当所有引擎都失败后才算该文件"转换失败"
- BatchProcessor 的重试是在 FallbackHandler 报告失败后，重新调用 FallbackHandler
- 重试时会使用相同的引擎选择逻辑，不强制指定某个引擎

### 3.6 进度报告

**位置:** `scripts/batch/reporter.py`

```python
class ProgressReporter:
    """进度报告器。"""

    def __init__(self, mode: str = "detailed"):
        """
        Args:
            mode: "silent" | "simple" | "detailed"
        """
        self.mode = mode
        self._pbar = None

    def start(self, total: int, desc: str = "Converting"):
        """开始进度跟踪。"""

    def update(self, file_path: str, status: str, **kwargs):
        """更新进度。"""

    def finish(self, result: BatchResult):
        """结束并输出报告。"""
```

**进度显示示例：**

```
Converting [###-----------] 15% 15/100  [00:32<03:12]  file1.pdf ✓
Converting [######---------] 30% 30/100  [01:05<02:30]  file2.pdf ✗ (retry)
Converting [######---------] 30% 30/100  [01:06<02:30]  file2.pdf ✗ (skip)
```

### 3.7 报告输出

**位置:** `scripts/batch/processor.py` (generate_reports)

**输出物：**

| 输出 | 文件名 | 内容 |
|------|--------|------|
| 汇总 | 控制台输出 | 成功/失败/跳过数量、耗时 |
| 详细日志 | `batch_conversion_YYYYMMDD_HHMMSS.log` | 每文件转换详情 |
| 失败清单 | `batch_conversion_YYYYMMDD_HHMMSS.failed` | 失败文件列表（可重跑） |

---

## 4. 文件结构

```
scripts/
├── batch/
│   ├── __init__.py
│   ├── __main__.py    # CLI 入口：python -m scripts.batch
│   ├── processor.py    # BatchProcessor 类
│   ├── result.py       # BatchResult, RetryPolicy, QueuedFile
│   ├── queue.py        # FileQueue
│   ├── strategies.py   # ConcurrencyStrategy, EngineAwareStrategy
│   └── reporter.py     # ProgressReporter
└── convert.py          # 现有代码（保持不变）
```

### 4.1 CLI 入口实现

**位置:** `scripts/batch/__main__.py`

```python
"""批量转换 CLI 入口。"""

import argparse
import sys
from .processor import BatchProcessor
from .result import RetryPolicy


def main():
    parser = argparse.ArgumentParser(description="批量文档转换工具")
    parser.add_argument("--input", "-i", required=True, help="输入源（文件/目录/通配符）")
    parser.add_argument("--output", "-o", required=True, help="输出目录")
    parser.add_argument("--patterns", nargs="+", default=["*.pdf", "*.docx", "*.pptx", "*.xlsx"], help="文件过滤模式")
    parser.add_argument("--concurrency", "-c", type=int, default=None, help="并发数，None 表示引擎感知")
    parser.add_argument("--progress", default="detailed", choices=["silent", "simple", "detailed"])
    parser.add_argument("--output-mode", default="preserve", choices=["flat", "preserve", "by_type"])
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有文件")
    parser.add_argument("--max-retries", type=int, default=1, help="最大重试次数")

    args = parser.parse_args()

    processor = BatchProcessor(
        concurrency=args.concurrency,
        retry_policy=RetryPolicy(max_retries=args.max_retries),
        progress_mode=args.progress,
        output_mode=args.output_mode,
    )

    result = processor.process_batch(
        input_sources=[args.input],
        output_dir=args.output,
        patterns=args.patterns,
        overwrite=args.overwrite,
    )

    # 输出汇总
    print(f"\n批量转换完成:")
    print(f"  成功: {result.succeeded}/{result.total}")
    print(f"  失败: {result.failed}")
    print(f"  跳过: {result.skipped}")
    print(f"  耗时: {result.duration_seconds:.2f}秒")

    sys.exit(0 if result.failed == 0 else 1)


if __name__ == "__main__":
    main()
```

---

## 5. CLI 集成

### 5.1 新增命令

```bash
# 基本批量转换
python -m scripts.batch --input dir/ --output out/

# 指定并发数
python -m scripts.batch --input dir/ --output out/ --concurrency 4

# 自定义文件模式
python -m scripts.batch --input dir/ --output out/ --patterns "*.pdf" "*.docx"

# 静默模式
python -m scripts.batch --input dir/ --output out/ --progress silent

# 覆盖已有文件
python -m scripts.batch --input dir/ --output out/ --overwrite
```

### 5.2 参数列表

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `--input` | 必填 | 输入源（文件/目录/通配符） |
| `--output` | 必填 | 输出目录 |
| `--patterns` | `*.pdf` 等 | 文件过滤模式 |
| `--concurrency` | `auto` | 并发数，`auto` 表示引擎感知 |
| `--progress` | `detailed` | 进度模式 |
| `--output-mode` | `preserve` | 输出模式 |
| `--overwrite` | `False` | 是否覆盖已有文件 |
| `--max-retries` | `1` | 最大重试次数 |

---

## 6. 测试策略

### 6.1 单元测试

| 测试文件 | 测试内容 |
|----------|----------|
| `test_queue.py` | 文件发现、通配符匹配、目录递归 |
| `test_strategies.py` | 引擎感知、固定并发 |
| `test_result.py` | BatchResult 序列化 |
| `test_reporter.py` | 进度输出格式 |

### 6.2 集成测试

| 测试文件 | 测试内容 |
|----------|----------|
| `test_batch_integration.py` | 端到端批量转换 |

---

## 7. 后续扩展

| 扩展方向 | 描述 |
|----------|------|
| 持久化队列 | 支持暂停/恢复批量任务 |
| 分布式处理 | 多机器协同批量处理 |
| 自适应并发 | 根据系统资源动态调整 |
| Webhook | 转换完成通知 |
