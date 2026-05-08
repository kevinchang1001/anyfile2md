# scripts/batch/processor.py
"""批量处理核心调度器。"""

import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from .result import BatchResult, FileConversionRecord, RetryPolicy, QueuedFile
from .queue import FileQueue
from .strategies import EngineAwareStrategy, FixedConcurrencyStrategy
from .reporter import ProgressReporter
from converters.fallback import FallbackHandler

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理调度器。"""

    def __init__(
        self,
        concurrency: Optional[int] = None,
        retry_policy: RetryPolicy = None,
        progress_mode: str = "detailed",
        output_mode: str = "preserve",
    ):
        self.concurrency = concurrency
        self.retry_policy = retry_policy or RetryPolicy.default()
        self.progress_mode = progress_mode
        self.output_mode = output_mode

        if concurrency is None:
            self._strategy = EngineAwareStrategy()
        else:
            self._strategy = FixedConcurrencyStrategy(concurrency)

        self._fallback_handler = FallbackHandler()
        self._file_queue = FileQueue()

    def process_batch(
        self,
        input_sources: list[str],
        output_dir: str,
        patterns: list[str] = None,
        overwrite: bool = False,
    ) -> BatchResult:
        start_time = time.time()

        if patterns:
            self._file_queue.patterns = patterns

        queued_files = self._file_queue.build_from_sources(
            sources=input_sources,
            output_dir=output_dir,
            output_mode=self.output_mode,
        )

        os.makedirs(output_dir, exist_ok=True)

        result = BatchResult(
            total=len(queued_files),
            succeeded=0,
            failed=0,
            skipped=0,
            duration_seconds=0,
            success_details=[],
            failure_details=[],
        )

        reporter = ProgressReporter(mode=self.progress_mode)
        reporter.start(total=len(queued_files), desc="Converting")

        # Group files by max_workers to enable proper concurrency
        # GPU files (max_workers=1) must be processed serially
        # CPU files can be processed in parallel
        file_groups: dict[int, list[QueuedFile]] = {}
        for qf in queued_files:
            if os.path.exists(qf.output_path) and not overwrite:
                reporter.update(qf.input_path, "skipped")
                result.skipped += 1
                continue

            max_workers = self._strategy.get_max_workers(qf.input_path)
            if max_workers not in file_groups:
                file_groups[max_workers] = []
            file_groups[max_workers].append(qf)

        # Process each group - files within a group can run concurrently
        for max_workers, files in file_groups.items():
            if max_workers == 1:
                # Serial processing for GPU files
                for qf in files:
                    success, record = self._convert_file_with_retry(qf)
                    if success:
                        result.succeeded += 1
                        result.success_details.append(record)
                        reporter.update(qf.input_path, "success")
                    else:
                        result.failed += 1
                        result.failure_details.append(record)
                        reporter.update(qf.input_path, "failed")
            else:
                # Parallel processing for CPU files
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_qf = {
                        executor.submit(self._convert_file_with_retry, qf): qf
                        for qf in files
                    }
                    for future in as_completed(future_to_qf):
                        qf = future_to_qf[future]
                        try:
                            success, record = future.result()
                            if success:
                                result.succeeded += 1
                                result.success_details.append(record)
                                reporter.update(qf.input_path, "success")
                            else:
                                result.failed += 1
                                result.failure_details.append(record)
                                reporter.update(qf.input_path, "failed")
                        except Exception as e:
                            result.failed += 1
                            record = FileConversionRecord(
                                input_path=qf.input_path,
                                output_path=qf.output_path,
                                engine="unknown",
                                quality_score=0,
                                duration_seconds=0,
                                error=str(e),
                                retry_count=0,
                            )
                            result.failure_details.append(record)
                            reporter.update(qf.input_path, "failed")

        reporter.finish(result)
        result.duration_seconds = time.time() - start_time
        self._generate_reports(result, output_dir)

        return result

    def _convert_file_with_retry(self, qf: QueuedFile) -> tuple[bool, FileConversionRecord]:
        attempt = 0
        max_attempts = self.retry_policy.max_retries + 1

        while attempt < max_attempts:
            try:
                conv_result, session = self._fallback_handler.convert_with_fallback(
                    input_path=qf.input_path,
                    output_path=qf.output_path,
                )

                if conv_result.success:
                    record = FileConversionRecord(
                        input_path=qf.input_path,
                        output_path=qf.output_path,
                        engine=session.final_engine or conv_result.engine,
                        quality_score=conv_result.quality_score,
                        duration_seconds=0,
                        error=None,
                        retry_count=attempt,
                    )
                    return True, record
                else:
                    error = conv_result.error

            except Exception as e:
                error = str(e)

            if attempt < max_attempts - 1:
                delay = self.retry_policy.get_retry_delay(attempt)
                time.sleep(delay)
                attempt += 1
            else:
                record = FileConversionRecord(
                    input_path=qf.input_path,
                    output_path=qf.output_path,
                    engine="unknown",
                    quality_score=0,
                    duration_seconds=0,
                    error=error,
                    retry_count=attempt,
                )
                return False, record

        return False, None

    def _generate_reports(self, result: BatchResult, output_dir: str):
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        log_file = os.path.join(output_dir, f"batch_conversion_{timestamp}.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Batch Conversion Log - {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total: {result.total}\n")
            f.write(f"Succeeded: {result.succeeded}\n")
            f.write(f"Failed: {result.failed}\n")
            f.write(f"Skipped: {result.skipped}\n")
            f.write(f"Duration: {result.duration_seconds:.2f}s\n\n")

            if result.success_details:
                f.write("Success Details:\n")
                f.write("-" * 60 + "\n")
                for rec in result.success_details:
                    f.write(f"  {rec.input_path} -> {rec.output_path} ({rec.engine}, score={rec.quality_score})\n")

            if result.failure_details:
                f.write("\nFailure Details:\n")
                f.write("-" * 60 + "\n")
                for rec in result.failure_details:
                    f.write(f"  {rec.input_path}: {rec.error} (retries={rec.retry_count})\n")

        result.log_file = log_file

        if result.failure_details:
            failed_file = os.path.join(output_dir, f"batch_conversion_{timestamp}.failed")
            with open(failed_file, "w", encoding="utf-8") as f:
                for rec in result.failure_details:
                    f.write(f"{rec.input_path}\n")
            result.failed_list_file = failed_file
