#!/usr/bin/env python3
"""
Check if markitdown is installed and accessible.

Usage:
    python check_dependency.py
"""

import shutil
import sys


def check_markitdown():
    """
    Check if markitdown command is available.

    Returns:
        True if markitdown is installed, False otherwise
    """
    result = shutil.which("markitdown")

    if result:
        print(f"markitdown found: {result}")
        return True
    else:
        print("markitdown not found in PATH")
        print("Install with: pip install markitdown")
        return False


def main():
    """Main entry point."""
    found = check_markitdown()
    sys.exit(0 if found else 1)


if __name__ == "__main__":
    main()
