# scripts/batch/__main__.py
"""批量转换 CLI 入口。"""

import argparse
import sys
import logging

from .processor import BatchProcessor
from .result import RetryPolicy

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


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

    try:
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

        print(f"\n批量转换完成:")
        print(f"  成功: {result.succeeded}/{result.total}")
        print(f"  失败: {result.failed}")
        print(f"  跳过: {result.skipped}")
        print(f"  耗时: {result.duration_seconds:.2f}秒")

        if result.log_file:
            print(f"  详细日志: {result.log_file}")
        if result.failed_list_file:
            print(f"  失败清单: {result.failed_list_file}")

        sys.exit(0 if result.failed == 0 else 1)

    except Exception as e:
        logging.error(f"批量转换失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()