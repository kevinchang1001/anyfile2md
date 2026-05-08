# scripts/batch/queue.py
"""文件队列管理器。"""

import os
import glob
from pathlib import Path
from typing import List

from .result import QueuedFile


class FileQueue:
    """文件队列管理器。"""

    def __init__(self, patterns: List[str] = None):
        self.patterns = patterns or ["*.pdf", "*.docx", "*.pptx", "*.xlsx"]

    def build_from_sources(
        self,
        sources: List[str],
        output_dir: str,
        output_mode: str = "preserve",
    ) -> List[QueuedFile]:
        files = []
        for source in sources:
            source = os.path.expanduser(source)
            if os.path.isfile(source):
                if self._matches_patterns(source):
                    files.append(self._create_queued_file(source, output_dir, output_mode))
            elif os.path.isdir(source):
                files.extend(self._scan_directory(source, output_dir, output_mode))
            else:
                files.extend(self._scan_glob(source, output_dir, output_mode))
        return files

    def _matches_patterns(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        for pattern in self.patterns:
            if pattern.startswith("*"):
                pattern_ext = pattern[1:].lower()
                if ext == pattern_ext:
                    return True
        return False

    def _scan_directory(self, directory: str, output_dir: str, output_mode: str) -> List[QueuedFile]:
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if self._matches_patterns(file_path):
                    files.append(self._create_queued_file(file_path, output_dir, output_mode))
        return files

    def _scan_glob(self, pattern: str, output_dir: str, output_mode: str) -> List[QueuedFile]:
        files = []
        for file_path in glob.glob(pattern):
            if os.path.isfile(file_path) and self._matches_patterns(file_path):
                files.append(self._create_queued_file(file_path, output_dir, output_mode))
        return files

    def _create_queued_file(self, input_path: str, output_dir: str, output_mode: str) -> QueuedFile:
        input_path = os.path.abspath(input_path)
        ext = os.path.splitext(input_path)[1].lower().lstrip(".")
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        relative_path = self._get_relative_path(input_path, output_dir, output_mode, ext, base_name)
        output_path = os.path.join(output_dir, relative_path)
        return QueuedFile(
            input_path=input_path,
            output_path=output_path,
            relative_path=relative_path,
        )

    def _get_relative_path(self, input_path: str, output_dir: str, output_mode: str, ext: str, base_name: str) -> str:
        if output_mode == "flat":
            return f"{base_name}.md"
        elif output_mode == "by_type":
            return f"{ext}/{base_name}.md"
        else:
            return f"{base_name}.md"