#!/bin/bash
#
# Install markitdown and optional plugins for anyfile2md plugin.
#
# Usage:
#     bash scripts/install_deps.sh          # Install core markitdown
#     bash scripts/install_deps.sh --all    # Install all optional dependencies
#     bash scripts/install_deps.sh --mcp     # Install MCP server
#     bash scripts/install_deps.sh --ocr    # Install OCR plugin
#

set -e

echo "============================================"
echo "AnyFile2MD Dependency Installer"
echo "============================================"
echo ""

# Parse arguments
INSTALL_ALL=false
INSTALL_MCP=false
INSTALL_OCR=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            INSTALL_ALL=true
            shift
            ;;
        --mcp)
            INSTALL_MCP=true
            shift
            ;;
        --ocr)
            INSTALL_OCR=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--all|--mcp|--ocr]"
            exit 1
            ;;
    esac
done

# Check pip availability and version
echo "Checking pip..."
if ! command -v pip &> /dev/null; then
    echo "Error: pip not found. Please install Python and pip first."
    exit 1
fi

PIP_VERSION=$(pip --version 2>&1 | awk '{print $2}')
echo "pip version: $PIP_VERSION"

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

echo ""
echo "============================================"
echo "Installing markitdown core..."
echo "============================================"

pip install markitdown

echo ""
echo "--------------------------------------------"
echo "Verifying core installation..."
echo "--------------------------------------------"

if command -v markitdown &> /dev/null; then
    echo "✓ markitdown installed successfully!"
    markitdown --version || true
else
    echo "Warning: markitdown command not found in PATH after installation."
    echo "You may need to restart your terminal or add pip's bin directory to PATH."
fi

echo ""
echo "============================================"
echo "Installing format-specific dependencies..."
echo "============================================"

echo "Installing PDF, DOCX, PPTX, XLSX support..."
pip install 'markitdown[pdf,docx,pptx,xlsx]'

echo ""
echo "============================================"
echo "Optional Components"
echo "============================================"

# MCP Server
if [ "$INSTALL_MCP" = true ] || [ "$INSTALL_ALL" = true ]; then
    echo ""
    echo "--------------------------------------------"
    echo "Installing MCP server (markitdown-mcp)..."
    echo "--------------------------------------------"
    pip install markitdown-mcp

    if command -v markitdown-mcp &> /dev/null; then
        echo "✓ markitdown-mcp installed successfully!"
    else
        echo "Warning: markitdown-mcp not found after installation."
    fi
fi

# OCR Plugin
if [ "$INSTALL_OCR" = true ] || [ "$INSTALL_ALL" = true ]; then
    echo ""
    echo "--------------------------------------------"
    echo "Installing OCR plugin (markitdown-ocr)..."
    echo "--------------------------------------------"
    echo "Note: OCR requires an OpenAI-compatible API key or Azure Document Intelligence."
    pip install markitdown-ocr

    echo ""
    echo "To use OCR, configure your LLM client:"
    echo "  export OPENAI_API_KEY=your_key"
    echo "  # or use Azure Document Intelligence endpoint"
    fi

# Full installation
if [ "$INSTALL_ALL" = true ]; then
    echo ""
    echo "--------------------------------------------"
    echo "Installing all optional dependencies..."
    echo "--------------------------------------------"
    pip install 'markitdown[all]'
fi

echo ""
echo "============================================"
echo "Installation Summary"
echo "============================================"
echo ""
echo "Installed components:"
echo "  ✓ markitdown (core)"
echo "  ✓ PDF support"
echo "  ✓ DOCX support"
echo "  ✓ PPTX support"
echo "  ✓ XLSX support"

if [ "$INSTALL_MCP" = true ] || [ "$INSTALL_ALL" = true ]; then
    echo "  ✓ markitdown-mcp (MCP server)"
fi

if [ "$INSTALL_OCR" = true ] || [ "$INSTALL_ALL" = true ]; then
    echo "  ✓ markitdown-ocr (OCR plugin)"
fi

echo ""
echo "============================================"
echo "Installation complete!"
echo "============================================"
echo ""
echo "Quick start:"
echo "  markitdown file.pdf -o output.md          # Convert single file"
echo "  markitdown --list-plugins                 # List installed plugins"
echo ""
echo "MCP server (if installed):"
echo "  markitdown-mcp                           # Start in STDIO mode"
echo "  markitdown-mcp --http --port 3001       # Start in HTTP mode"
