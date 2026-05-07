#!/usr/bin/env python3
"""
Single file conversion to Markdown using markitdown.

Usage:
    python convert.py --input <file> --output <output.md>
    python convert.py -i <file> -o <output.md>

Configuration:
    Create anyfile2md.config.local.md in project root:
        input_dir: "./input_files"
        output_dir: "./output_markdown"
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Import config loader
try:
    from config_loader import load_config, SUPPORTED_EXTENSIONS, get_format_description
except ImportError:
    # Fallback if config_loader not available
    def load_config():
        return {"input_dir": "./input_files", "output_dir": "./output_markdown"}

    SUPPORTED_EXTENSIONS = {
        '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
        '.pdf', '.html', '.htm', '.png', '.jpg', '.jpeg',
        '.gif', '.bmp', '.webp', '.csv', '.json', '.xml',
        '.zip', '.epub', '.ipynb', '.rtf', '.txt', '.md'
    }

    def get_format_description(ext):
        return ext.upper()

# Import engine registry
try:
    from converters import (
        EngineRegistry,
        get_default_engine,
        select_best_engine,
        BaseConverter,
        ConversionResult,
    )
except ImportError:
    # Fallback if converters not available
    EngineRegistry = None

    def get_default_engine():
        return None

    def select_best_engine(path):
        return None, 0.0

    class BaseConverter:
        pass

    class ConversionResult:
        pass

CONVERSION_TIMEOUT: int = 60  # seconds


def convert_file(input_path: str, output_path: str, enable_plugins: bool = False) -> bool:
    """
    Convert a single file to Markdown.

    Args:
        input_path: Path to input file
        output_path: Path to output markdown file
        enable_plugins: Whether to enable markitdown plugins

    Returns:
        True if conversion successful, False otherwise
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return False

    ext = input_file.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"Error: Unsupported file format: {ext}", file=sys.stderr)
        print(f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}", file=sys.stderr)
        return False

    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        cmd = ["markitdown", str(input_file)]

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
            print(f"Successfully converted: {input_file} -> {output_file}")
            return True
        else:
            print(f"Conversion failed: {result.stderr}", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"Error: Conversion timeout ({CONVERSION_TIMEOUT}s)", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: markitdown not found. Run 'bash scripts/install_deps.sh' to install.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert a single file to Markdown using markitdown"
    )
    parser.add_argument(
        "--input", "-i",
        help="Input file path"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output markdown file path"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Load input/output from config file"
    )
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="Enable markitdown plugins (for OCR, etc.)"
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List all supported formats"
    )
    parser.add_argument(
        "-e", "--engine",
        choices=["markitdown", "mineru", "auto"],
        default="auto",
        help="Converter engine: markitdown, mineru, or auto (default)"
    )
    parser.add_argument(
        "--list-engines",
        action="store_true",
        help="List available converter engines"
    )

    args = parser.parse_args()

    if args.list_engines:
        if EngineRegistry is None:
            print("Engine registry not available")
        else:
            registry = EngineRegistry()
            print("Available engines:")
            for name in registry.list_engines():
                print(f"  - {name}")
        return

    # Select engine based on --engine argument
    if args.engine == "auto":
        if EngineRegistry is not None:
            engine, conf = select_best_engine(args.input or "")
            if engine:
                print(f"Auto-selected engine: {engine.name} (confidence: {conf:.2f})")
    else:
        if EngineRegistry is not None:
            registry = EngineRegistry()
            engine = registry.get_engine(args.engine)
            if engine is None:
                print(f"Error: Unknown engine: {args.engine}")
                sys.exit(1)
            if not engine.is_available():
                print(f"Error: Engine '{args.engine}' is not available")
                sys.exit(1)
            print(f"Using engine: {args.engine}")

    if args.list_formats:
        print("Supported formats:")
        for ext in sorted(SUPPORTED_EXTENSIONS):
            desc = get_format_description(ext)
            print(f"  {ext}: {desc}")
        return

    # If --config is used, try to use config-based paths
    if args.config or (not args.input and not args.output):
        config = load_config()
        if not args.input:
            args.input = str(Path(config["input_dir"]) / "input.md")
        if not args.output:
            args.output = str(Path(config["output_dir"]) / "output.md")

    if not args.input or not args.output:
        parser.print_help()
        sys.exit(1)

    success = convert_file(args.input, args.output, args.plugins)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
