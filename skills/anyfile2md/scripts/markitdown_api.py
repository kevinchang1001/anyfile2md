#!/usr/bin/env python3
"""
MarkItDown Python API wrapper for anyfile2md.

Provides direct Python interface to MarkItDown class.

Usage:
    python markitdown_api.py --input file.pdf --output file.md
    python markitdown_api.py --input file.pdf --output file.md --plugins
    python markitdown_api.py --input file.pdf --output file.md --llm-client openai --llm-model gpt-4o
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from markitdown import MarkItDown
    from openai import OpenAI
except ImportError:
    print("Error: markitdown not installed. Run 'pip install markitdown'", file=sys.stderr)
    print("For LLM support: pip install openai", file=sys.stderr)
    sys.exit(1)


def convert_with_api(
    input_path: str,
    output_path: str,
    enable_plugins: bool = False,
    llm_client=None,
    llm_model: Optional[str] = None,
    llm_prompt: Optional[str] = None,
    docintel_endpoint: Optional[str] = None,
    docintel_credential: Optional[str] = None,
) -> bool:
    """
    Convert file using MarkItDown Python API.

    Args:
        input_path: Input file path
        output_path: Output markdown file path
        enable_plugins: Enable markitdown plugins
        llm_client: OpenAI or compatible LLM client
        llm_model: LLM model name
        llm_prompt: Custom prompt for image description
        docintel_endpoint: Azure Document Intelligence endpoint
        docintel_credential: Azure credential

    Returns:
        True if conversion successful, False otherwise
    """
    try:
        md = MarkItDown(
            enable_plugins=enable_plugins,
            llm_client=llm_client,
            llm_model=llm_model,
            llm_prompt=llm_prompt,
            docintel_endpoint=docintel_endpoint,
            docintel_credential=docintel_credential,
        )

        result = md.convert(input_path)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.text_content, encoding='utf-8')

        print(f"Successfully converted: {input_path} -> {output_path}")
        print(f"Output size: {len(result.text_content)} characters")
        return True

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert files to Markdown using MarkItDown Python API"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input file path"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output markdown file path"
    )
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="Enable markitdown plugins (for OCR)"
    )
    parser.add_argument(
        "--llm-client",
        choices=["openai", "azure"],
        help="LLM client type for image description"
    )
    parser.add_argument(
        "--llm-model",
        help="LLM model name (e.g., gpt-4o)"
    )
    parser.add_argument(
        "--llm-prompt",
        help="Custom prompt for image description"
    )
    parser.add_argument(
        "--docintel-endpoint",
        help="Azure Document Intelligence endpoint"
    )
    parser.add_argument(
        "--api-key",
        help="API key for the LLM service"
    )

    args = parser.parse_args()

    # Setup LLM client if requested
    llm_client = None
    if args.llm_client:
        if args.llm_client == "openai":
            api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("Error: OPENAI_API_KEY not set. Use --api-key or set environment variable.")
                sys.exit(1)
            llm_client = OpenAI(api_key=api_key)

    success = convert_with_api(
        args.input,
        args.output,
        enable_plugins=args.plugins,
        llm_client=llm_client,
        llm_model=args.llm_model,
        llm_prompt=args.llm_prompt,
        docintel_endpoint=args.docintel_endpoint,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
