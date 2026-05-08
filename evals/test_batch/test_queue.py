import pytest
import tempfile
import os
import sys
sys.path.insert(0, "scripts")
from batch.queue import FileQueue, QueuedFile


def test_file_queue_init():
    q = FileQueue()
    assert q.patterns == ["*.pdf", "*.docx", "*.pptx", "*.xlsx"]


def test_file_queue_custom_patterns():
    q = FileQueue(patterns=["*.pdf"])
    assert q.patterns == ["*.pdf"]


def test_build_from_single_file():
    q = FileQueue()
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.pdf")
        open(test_file, "w").close()
        result = q.build_from_sources([test_file], tmpdir)
        assert len(result) == 1
        assert result[0].input_path == test_file


def test_build_from_directory():
    q = FileQueue(patterns=["*.pdf"])
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)
        open(os.path.join(subdir, "a.pdf"), "w").close()
        open(os.path.join(subdir, "b.pdf"), "w").close()
        open(os.path.join(tmpdir, "c.pdf"), "w").close()
        result = q.build_from_sources([tmpdir], tmpdir, output_mode="preserve")
        assert len(result) == 3


def test_build_from_glob_pattern():
    q = FileQueue(patterns=["*.pdf"])
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "a.pdf"), "w").close()
        open(os.path.join(tmpdir, "b.pdf"), "w").close()
        open(os.path.join(tmpdir, "c.txt"), "w").close()
        result = q.build_from_sources([os.path.join(tmpdir, "*.pdf")], tmpdir)
        assert len(result) == 2


def test_output_mode_flat():
    q = FileQueue(patterns=["*.pdf"])
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)
        open(os.path.join(subdir, "a.pdf"), "w").close()
        result = q.build_from_sources([subdir], tmpdir, output_mode="flat")
        assert len(result) == 1
        assert result[0].relative_path == "a.md"


def test_output_mode_by_type():
    q = FileQueue(patterns=["*.pdf", "*.docx"])
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "a.pdf"), "w").close()
        open(os.path.join(tmpdir, "b.docx"), "w").close()
        result = q.build_from_sources([tmpdir], tmpdir, output_mode="by_type")
        assert len(result) == 2
        paths = {r.relative_path for r in result}
        assert "pdf/a.md" in paths
        assert "docx/b.md" in paths