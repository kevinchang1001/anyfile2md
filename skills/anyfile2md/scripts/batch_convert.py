#!/usr/bin/env python3
"""
Batch conversion of files to Markdown using markitdown.

Usage:
    python batch_convert.py --input-dir <dir> --output-dir <dir>
    python batch_convert.py -d <dir> -o <dir> [--recursive]

Configuration:
    Create anyfile2md.config.local.md in project root:
        input_dir: "./input_files"
        output_dir: "./output_markdown"
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Set, Tuple, List

# Import config loader
try:
    from config_loader import load_config, SUPPORTED_EXTENSIONS
except ImportError:
    def load_config():
        return {"input_dir": "./input_files", "output_dir": "./output_markdown"}

    SUPPORTED_EXTENSIONS = {
        '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
        '.pdf', '.html', '.htm', '.png', '.jpg', '.jpeg',
        '.gif', '.bmp', '.webp', '.csv', '.json', '.xml',
        '.zip', '.epub', '.ipynb', '.rtf', '.txt', '.md'
    }

CONVERSION_TIMEOUT: int = 60  # seconds per file


def find_files(directory: Path, recursive: bool = False) -> list:
    """
    Find all supported files in directory.

    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories

    Returns:
        List of Path objects for supported files
    """
    if not directory.exists():
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        return []

    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}", file=sys.stderr)
        return []

    files = []

    if recursive:
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(directory.rglob(f"*{ext}"))
            files.extend(directory.rglob(f"*{ext.upper()}"))
    else:
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(item)

    return sorted(files)


def get_relative_path(file_path: Path, base_dir: Path) -> Path:
    """
    Get relative path from base directory.

    Args:
        file_path: Full path to file
        base_dir: Base directory

    Returns:
        Relative path preserving directory structure
    """
    try:
        return file_path.relative_to(base_dir)
    except ValueError:
        return Path(file_path.name)


def convert_file(
    input_path: Path,
    output_dir: Path,
    base_input_dir: Path,
    overwrite: bool = False,
    enable_plugins: bool = False
) -> Tuple[bool, str]:
    """
    Convert a single file to Markdown.

    Args:
        input_path: Path to input file
        output_dir: Base output directory
        base_input_dir: Base input directory for relative path calculation
        overwrite: Whether to overwrite existing files
        enable_plugins: Whether to enable markitdown plugins

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Preserve directory structure
    rel_path = get_relative_path(input_path, base_input_dir)
    output_subdir = output_dir / rel_path.parent
    output_file = output_subdir / f"{input_path.stem}.md"

    if output_file.exists() and not overwrite:
        return True, f"Skipped (exists): {rel_path}"

    output_subdir.mkdir(parents=True, exist_ok=True)

    try:
        cmd = ["markitdown", str(input_path)]

        if enable_plugins:
            cmd.append("--use-plugins")

        cmd.extend(["-o", str(output_file)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT
        )

        if result.returncode == 0:
            return True, f"Converted: {rel_path} -> {output_file.name}"
        else:
            error_msg = result.stderr[:100] if result.stderr else "Unknown error"
            return False, f"Failed: {rel_path} - {error_msg}"

    except subprocess.TimeoutExpired:
        return False, f"Timeout ({CONVERSION_TIMEOUT}s): {rel_path}"
    except FileNotFoundError:
        return False, "Error: markitdown not found. Run 'bash scripts/install_deps.sh'"
    except Exception as e:
        return False, f"Error: {rel_path} - {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert files to Markdown using markitdown"
    )
    parser.add_argument(
        "--input-dir", "-d",
        help="Input directory containing files to convert"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="Output directory for converted Markdown files"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively process subdirectories"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Load input/output directories from config file"
    )
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="Enable markitdown plugins (for OCR, etc.)"
    )

    args = parser.parse_args()

    # Load config if requested or if dirs not provided
    if args.config or (not args.input_dir and not args.output_dir):
        config = load_config()
        args.input_dir = args.input_dir or config["input_dir"]
        args.output_dir = args.output_dir or config["output_dir"]

    if not args.input_dir or not args.output_dir:
        parser.print_help()
        sys.exit(1)

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    print(f"Scanning: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Recursive: {args.recursive}")
    print(f"Plugins: {args.plugins}")
    print(f"Timeout: {CONVERSION_TIMEOUT}s per file")
    print("-" * 60)

    files = find_files(input_dir, args.recursive)

    if not files:
        print("No supported files found.")
        print(f"\nSupported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        sys.exit(0)

    print(f"Found {len(files)} file(s) to convert")
    print("-" * 60)

    results: List[Tuple[bool, str]] = []

    for file_path in files:
        success, message = convert_file(
            file_path,
            output_dir,
            input_dir,
            args.overwrite,
            args.plugins
        )
        results.append((success, message))
        print(message)

    # Summary report
    print("-" * 60)
    print("=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)

    success_list = [msg for success, msg in results if success]
    fail_list = [msg for success, msg in results if not success]

    print(f"Total: {len(results)} | Success: {len(success_list)} | Failed: {len(fail_list)}")

    if fail_list:
        print("\nFAILED FILES:")
        for msg in fail_list:
            print(f"  - {msg}")

    if success_list:
        print("\nSUCCESSFUL FILES:")
        for msg in success_list[:10]:  # Show first 10
            print(f"  + {msg}")
        if len(success_list) > 10:
            print(f"  ... and {len(success_list) - 10} more")

    sys.exit(0 if len(fail_list) == 0 else 1)


if __name__ == "__main__":
    main()
