import pytest
import tempfile
import os
import sys
sys.path.insert(0, "scripts")
from batch import BatchProcessor
from batch.result import RetryPolicy


def test_batch_processor_end_to_end():
    """端到端测试：创建测试文件 -> 批量转换 -> 验证结果。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = os.path.join(tmpdir, "input")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # 创建测试 PDF 文件（空文件即可）
        test_file = os.path.join(input_dir, "test.pdf")
        with open(test_file, "wb") as f:
            f.write(b"%PDF-1.4 test")

        processor = BatchProcessor(
            concurrency=1,
            retry_policy=RetryPolicy(max_retries=0),
            progress_mode="silent",
        )

        result = processor.process_batch(
            input_sources=[input_dir],
            output_dir=output_dir,
            patterns=["*.pdf"],
        )

        # 验证结果结构
        assert result.total >= 0
        assert result.succeeded + result.failed + result.skipped == result.total
        assert result.duration_seconds >= 0