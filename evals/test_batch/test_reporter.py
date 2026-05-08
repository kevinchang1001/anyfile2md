import pytest
import sys
sys.path.insert(0, "scripts")
from batch.reporter import ProgressReporter
from batch.result import BatchResult, FileConversionRecord


def test_progress_reporter_init():
    reporter = ProgressReporter()
    assert reporter.mode == "detailed"


def test_progress_reporter_silent_mode():
    reporter = ProgressReporter(mode="silent")
    assert reporter.mode == "silent"


def test_progress_reporter_simple_mode():
    reporter = ProgressReporter(mode="simple")
    assert reporter.mode == "simple"


def test_progress_reporter_start():
    reporter = ProgressReporter(mode="silent")
    reporter.start(total=10, desc="Testing")
    assert reporter._total == 10
    assert reporter._current == 0


def test_progress_reporter_update():
    reporter = ProgressReporter(mode="silent")
    reporter.start(total=10)
    reporter.update("file.pdf", "success")
    assert reporter._current == 1