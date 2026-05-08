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
    from converters.complexity import ComplexityDetector
    from converters.fallback import FallbackHandler
    from converters.errors import ConversionSession
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

    FallbackHandler = None
    ConversionSession = None

CONVERSION_TIMEOUT: int = 60  # seconds


def convert_file(input_path: str, output_path: str, enable_plugins: bool = False, engine=None) -> bool:
    """
    Convert a single file to Markdown.

    Args:
        input_path: Path to input file
        output_path: Path to output markdown file
        enable_plugins: Whether to enable markitdown plugins (for fallback subprocess only)
        engine: BaseConverter instance to use for conversion (optional)

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

    # Use engine.convert() if engine is provided and available
    if engine is not None and isinstance(engine, BaseConverter) and engine.is_available():
        result = engine.convert(str(input_file), str(output_file))
        if result.success:
            print(f"Successfully converted: {input_file} -> {output_file} (engine: {engine.name})")
            return True
        else:
            print(f"Conversion failed: {result.error}", file=sys.stderr)
            return False

    # Fallback to markitdown subprocess
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
    parser.add_argument(
        "--auto-select",
        action="store_true",
        help="Force complexity-based engine selection"
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        default=True,
        help="Enable automatic fallback to other engines on failure (default: enabled)"
    )

    args = parser.parse_args()

    # Initialize engine to None (will be set based on --engine argument)
    engine = None

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

    # Show complexity info if --auto-select
    if args.auto_select and args.input and Path(args.input).suffix.lower() == ".pdf":
        try:
            detector = ComplexityDetector()
            complexity = detector.analyze(args.input)
            print(f"Complexity: {complexity.score} ({', '.join(complexity.factors.keys()) or 'simple'})")
            print(f"Recommended: {complexity.recommended_engine}")
        except Exception as e:
            print(f"Complexity analysis failed: {e}", file=sys.stderr)

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

    # Check if file format is supported before attempting conversion
    if args.input:
        input_ext = Path(args.input).suffix.lower()
        if input_ext not in SUPPORTED_EXTENSIONS:
            print(f"Error: Unsupported file format: {input_ext}", file=sys.stderr)
            print(f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}", file=sys.stderr)
            sys.exit(1)

    # Use fallback handler for conversion if enabled and available
    if args.fallback and FallbackHandler is not None and args.input:
        handler = FallbackHandler()

        result, session = handler.convert_with_fallback(
            args.input,
            args.output,
            preferred_engine=args.engine if args.engine != "auto" else None
        )

        # Show what happened
        if len(session.attempts) > 1:
            print(f"Tried {len(session.attempts)} engines:")
            for attempt in session.attempts:
                status = "success" if attempt.success else "failed"
                print(f"  - {attempt.engine}: {status}")

        if result.success:
            print(f"Successfully converted: {args.input} -> {args.output}")
            sys.exit(0)
        else:
            print(f"Conversion failed: {result.error}", file=sys.stderr)
            sys.exit(1)
    else:
        # Use single engine without fallback (existing logic)
        success = convert_file(args.input, args.output, args.plugins, engine)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
