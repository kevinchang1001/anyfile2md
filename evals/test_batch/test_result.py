import pytest
import sys
sys.path.insert(0, "scripts")
from batch.result import BatchResult, FileConversionRecord, RetryPolicy, QueuedFile


def test_retry_policy_default():
    policy = RetryPolicy.default()
    assert policy.max_retries == 1
    assert policy.retry_delay == 1.0
    assert policy.exponential_backoff is False


def test_retry_policy_exponential_backoff():
    policy = RetryPolicy(max_retries=3, retry_delay=1.0, exponential_backoff=True, max_delay=30.0)
    assert policy.get_retry_delay(0) == 1.0
    assert policy.get_retry_delay(1) == 2.0
    assert policy.get_retry_delay(2) == 4.0
    assert policy.get_retry_delay(10) == 30.0


def test_batch_result_structure():
    result = BatchResult(
        total=10,
        succeeded=8,
        failed=1,
        skipped=1,
        duration_seconds=120.5,
        success_details=[],
        failure_details=[],
    )
    assert result.total == 10
    assert result.succeeded == 8
    assert result.failed == 1


def test_file_conversion_record():
    record = FileConversionRecord(
        input_path="/input/file.pdf",
        output_path="/output/file.md",
        engine="mineru",
        quality_score=85,
        duration_seconds=5.2,
    )
    assert record.error is None
    assert record.retry_count == 0


def test_queued_file():
    qf = QueuedFile(
        input_path="/input/subdir/file.pdf",
        output_path="/output/subdir/file.md",
        relative_path="subdir/file.md",
    )
    assert qf.relative_path == "subdir/file.md"