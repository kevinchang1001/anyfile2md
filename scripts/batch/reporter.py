# scripts/batch/reporter.py
"""进度报告器。"""

from typing import Optional

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from .result import BatchResult


class ProgressReporter:
    """进度报告器。"""

    def __init__(self, mode: str = "detailed"):
        """
        Args:
            mode: 进度模式 ("silent", "simple", "detailed")
        """
        self.mode = mode
        self._pbar = None
        self._total = 0
        self._current = 0

    def start(self, total: int, desc: str = "Converting"):
        """开始进度跟踪。"""
        self._total = total
        self._current = 0

        if self.mode == "silent":
            return

        if TQDM_AVAILABLE and self.mode == "detailed":
            self._pbar = tqdm(total=total, desc=desc, unit="file")
        elif self.mode == "simple":
            print(f"{desc}: 0/{total}")

    def update(self, file_path: str, status: str, **kwargs):
        """更新进度。"""
        self._current += 1

        if self.mode == "silent":
            return

        if self._pbar:
            status_icon = self._get_status_icon(status)
            self._pbar.set_postfix_str(f"{status_icon} {file_path}")
            self._pbar.update(1)
        elif self.mode == "simple":
            print(f"  {self._current}/{self._total} {file_path}: {status}")

    def _get_status_icon(self, status: str) -> str:
        """获取状态图标。"""
        icons = {
            "success": "✓",
            "failed": "✗",
            "skipped": "○",
            "retry": "↻",
        }
        return icons.get(status, "?")

    def finish(self, result: BatchResult):
        """结束并输出报告。"""
        if self._pbar:
            self._pbar.close()

        if self.mode == "silent":
            return

        print(f"\n批量转换完成:")
        print(f"  成功: {result.succeeded}/{result.total}")
        print(f"  失败: {result.failed}")
        print(f"  跳过: {result.skipped}")
        print(f"  耗时: {result.duration_seconds:.2f}秒")