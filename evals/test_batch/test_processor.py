import pytest
import tempfile
import os
import sys
sys.path.insert(0, "scripts")
from batch.processor import BatchProcessor
from batch.result import RetryPolicy


def test_batch_processor_init():
    processor = BatchProcessor()
    assert processor.concurrency is None
    assert processor.retry_policy == RetryPolicy.default()
    assert processor.progress_mode == "detailed"
    assert processor.output_mode == "preserve"


def test_batch_processor_custom_init():
    processor = BatchProcessor(
        concurrency=4,
        retry_policy=RetryPolicy(max_retries=2),
        progress_mode="silent",
        output_mode="flat",
    )
    assert processor.concurrency == 4
    assert processor.retry_policy.max_retries == 2
    assert processor.progress_mode == "silent"
    assert processor.output_mode == "flat"
