#!/usr/bin/env python3
"""
Configuration loader for anyfile2md.

Loads settings from anyfile2md.config.local.md in project root.

Usage:
    from config_loader import load_config
    config = load_config()
"""

import sys
from pathlib import Path
from typing import Optional

CONFIG_FILENAME = "anyfile2md.config.local.md"

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    # Office Documents
    '.docx', '.doc',           # Word
    '.xlsx', '.xls',           # Excel
    '.pptx', '.ppt',           # PowerPoint
    # Documents
    '.pdf',                    # PDF
    '.rtf',                    # Rich Text Format
    # Web
    '.html', '.htm',           # HTML
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.tif',
    # Data formats
    '.csv',                    # CSV
    '.json',                   # JSON
    '.xml',                    # XML
    # Archives
    '.zip',                    # ZIP (recursive)
    # eBooks
    '.epub',                   # EPUB
    # Code/Ide
    '.ipynb',                  # Jupyter Notebook
    # Other
    '.txt',                    # Plain text
    '.md',                     # Markdown
    '.yaml', '.yml',           # YAML
    '.toml',                  # TOML
}

# Extensions requiring optional dependencies
OPTIONAL_EXTENSIONS = {
    '.pdf': ['pdfminer.six', 'pdfplumber'],
    '.docx': ['mammoth', 'lxml'],
    '.doc': ['mammoth', 'lxml'],
    '.xlsx': ['pandas', 'openpyxl'],
    '.xls': ['pandas', 'xlrd'],
    '.pptx': ['python-pptx'],
    '.ppt': ['python-pptx'],
    '.zip': [],  # Built-in
    '.epub': [],  # Built-in
    '.ipynb': [],  # Built-in
    '.csv': [],  # Built-in
    '.json': [],  # Built-in
    '.xml': ['defusedxml'],
}


def find_config_file() -> Optional[Path]:
    """
    Find config file by searching up from current directory.

    Search order:
    1. Current working directory
    2. Parent directories up to repo root
    3. .claude/ directory

    Returns:
        Path to config file if found, None otherwise
    """
    cwd = Path.cwd()

    # Search current and parent directories
    for directory in [cwd] + list(cwd.parents):
        config_path = directory / CONFIG_FILENAME
        if config_path.exists():
            return config_path

        # Also check .claude/ subdirectory
        claude_dir = directory / ".claude"
        if claude_dir.exists():
            config_path = claude_dir / CONFIG_FILENAME
            if config_path.exists():
                return config_path

    return None


def parse_config(content: str) -> dict:
    """
    Parse YAML-like config content.

    Args:
        content: Config file content

    Returns:
        Dictionary with input_dir and output_dir
    """
    config = {
        "input_dir": "./input_files",
        "output_dir": "./output_markdown"
    }

    for line in content.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if key in ('input_dir', 'output_dir'):
                config[key] = value

    return config


def load_config() -> dict:
    """
    Load configuration from anyfile2md.config.local.md.

    Returns:
        Dictionary with input_dir and output_dir
        Defaults if no config file found
    """
    config_file = find_config_file()

    if config_file is None:
        return {
            "input_dir": "./input_files",
            "output_dir": "./output_markdown",
            "config_file": None
        }

    try:
        content = config_file.read_text(encoding='utf-8')
        config = parse_config(content)
        config["config_file"] = str(config_file)
        return config
    except Exception as e:
        print(f"Warning: Failed to read config file: {e}", file=sys.stderr)
        return {
            "input_dir": "./input_files",
            "output_dir": "./output_markdown",
            "config_file": None
        }


def get_supported_extensions() -> set:
    """Return set of all supported file extensions."""
    return SUPPORTED_EXTENSIONS.copy()


def get_format_description(ext: str) -> str:
    """Get human-readable format description."""
    descriptions = {
        '.docx': 'Word Document',
        '.doc': 'Word Document (Legacy)',
        '.xlsx': 'Excel Spreadsheet',
        '.xls': 'Excel Spreadsheet (Legacy)',
        '.pptx': 'PowerPoint Presentation',
        '.ppt': 'PowerPoint Presentation (Legacy)',
        '.pdf': 'PDF Document',
        '.html': 'HTML Web Page',
        '.htm': 'HTML Web Page',
        '.png': 'PNG Image',
        '.jpg': 'JPEG Image',
        '.jpeg': 'JPEG Image',
        '.gif': 'GIF Image',
        '.bmp': 'Bitmap Image',
        '.webp': 'WebP Image',
        '.tiff': 'TIFF Image',
        '.tif': 'TIFF Image',
        '.csv': 'CSV Data',
        '.json': 'JSON Data',
        '.xml': 'XML Data',
        '.zip': 'ZIP Archive',
        '.epub': 'EPUB eBook',
        '.ipynb': 'Jupyter Notebook',
        '.rtf': 'Rich Text Format',
        '.txt': 'Plain Text',
        '.md': 'Markdown',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
    }
    return descriptions.get(ext.lower(), ext.upper())


if __name__ == "__main__":
    config = load_config()
    print(f"input_dir: {config['input_dir']}")
    print(f"output_dir: {config['output_dir']}")
    if config['config_file']:
        print(f"config_file: {config['config_file']}")
    else:
        print("config_file: (using defaults)")

    print(f"\nSupported formats ({len(SUPPORTED_EXTENSIONS)}):")
    for ext in sorted(SUPPORTED_EXTENSIONS):
        desc = get_format_description(ext)
        optional = " [需要可选依赖]" if ext in OPTIONAL_EXTENSIONS else ""
        print(f"  {ext}: {desc}{optional}")
