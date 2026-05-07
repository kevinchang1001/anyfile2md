#!/usr/bin/env python3
"""
Unit tests for anyfile2md conversion scripts.

Run with: python -m pytest evals/test_conversion.py -v
Or directly: python evals/test_conversion.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

# Test configuration
SKILLS_DIR = Path(__file__).parent.parent / "skills" / "anyfile2md"
SCRIPTS_DIR = SKILLS_DIR / "scripts"

# Scripts
CONVERT_SCRIPT = SCRIPTS_DIR / "convert.py"
BATCH_SCRIPT = SCRIPTS_DIR / "batch_convert.py"
CHECK_SCRIPT = SCRIPTS_DIR / "check_dependency.py"


class TestDependencyCheck:
    """Test markitdown dependency verification."""

    def test_check_dependency_runs(self):
        """Check dependency script executes without error."""
        result = subprocess.run(
            [sys.executable, str(CHECK_SCRIPT)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "markitdown" in result.stdout.lower()

    def test_markitdown_command_available(self):
        """Verify markitdown command is in PATH."""
        result = subprocess.run(["markitdown", "--version"], capture_output=True)
        assert result.returncode == 0, "markitdown not found in PATH"


def test_convert_with_engine_flag():
    """convert.py accepts --engine parameter."""
    result = subprocess.run(
        ["python", str(CONVERT_SCRIPT), "--help"],
        capture_output=True,
        text=True
    )
    assert "--engine" in result.stdout or "-e" in result.stdout

def test_convert_list_engines():
    """convert.py --list-engines shows available engines."""
    result = subprocess.run(
        ["python", str(CONVERT_SCRIPT), "--list-engines"],
        capture_output=True,
        text=True
    )
    assert "markitdown" in result.stdout.lower()


class TestConvertScript:
    """Test single file conversion."""

    def setup_method(self):
        """Create temp directories for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()

    def teardown_method(self):
        """Clean up temp directories."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_convert_html_success(self):
        """Test successful HTML to Markdown conversion."""
        # Create test HTML file
        html_file = self.input_dir / "test.html"
        html_file.write_text("<h1>Test</h1><p>Hello World</p>")

        output_file = self.output_dir / "test.md"

        result = subprocess.run(
            [sys.executable, str(CONVERT_SCRIPT),
             "-i", str(html_file), "-o", str(output_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Conversion failed: {result.stderr}"
        assert output_file.exists(), "Output file not created"
        assert "# Test" in output_file.read_text()

    def test_convert_unsupported_format(self):
        """Test conversion fails gracefully for unsupported format."""
        input_file = self.input_dir / "test.xyz"
        input_file.write_text("dummy content")

        output_file = self.output_dir / "test.md"

        result = subprocess.run(
            [sys.executable, str(CONVERT_SCRIPT),
             "-i", str(input_file), "-o", str(output_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "Unsupported" in result.stderr or "not supported" in result.stderr.lower()

    def test_convert_missing_input(self):
        """Test conversion fails gracefully for missing file."""
        input_file = self.input_dir / "nonexistent.pdf"
        output_file = self.output_dir / "test.md"

        result = subprocess.run(
            [sys.executable, str(CONVERT_SCRIPT),
             "-i", str(input_file), "-o", str(output_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestBatchConvert:
    """Test batch directory conversion."""

    def setup_method(self):
        """Create temp directories for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()

    def teardown_method(self):
        """Clean up temp directories."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_batch_convert_basic(self):
        """Test basic batch conversion of multiple files."""
        # Create test files
        (self.input_dir / "doc1.html").write_text("<h1>Doc 1</h1>")
        (self.input_dir / "doc2.html").write_text("<h2>Doc 2</h2>")

        result = subprocess.run(
            [sys.executable, str(BATCH_SCRIPT),
             "-d", str(self.input_dir), "-o", str(self.output_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Batch failed: {result.stderr}"
        assert (self.output_dir / "doc1.md").exists()
        assert (self.output_dir / "doc2.md").exists()

    def test_batch_convert_preserves_structure(self):
        """Test batch conversion preserves subdirectory structure."""
        # Create nested structure
        subdir = self.input_dir / "subdir"
        subdir.mkdir()
        (self.input_dir / "doc1.html").write_text("<h1>Root</h1>")
        (subdir / "doc2.html").write_text("<h1>Subdir</h1>")

        result = subprocess.run(
            [sys.executable, str(BATCH_SCRIPT),
             "-d", str(self.input_dir), "-o", str(self.output_dir),
             "--recursive"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert (self.output_dir / "doc1.md").exists()
        assert (self.output_dir / "subdir" / "doc2.md").exists()

    def test_batch_convert_no_supported_files(self):
        """Test batch conversion handles empty directory gracefully."""
        result = subprocess.run(
            [sys.executable, str(BATCH_SCRIPT),
             "-d", str(self.input_dir), "-o", str(self.output_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "No supported files found" in result.stdout


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Create temp directories for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()

    def teardown_method(self):
        """Clean up temp directories."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_skip_existing_files(self):
        """Test that existing files are skipped by default."""
        html_file = self.input_dir / "test.html"
        html_file.write_text("<h1>Original</h1>")

        output_file = self.output_dir / "test.md"
        output_file.write_text("# Already exists")

        result = subprocess.run(
            [sys.executable, str(BATCH_SCRIPT),
             "-d", str(self.input_dir), "-o", str(self.output_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Skipped" in result.stdout
        # Content should not be overwritten
        assert output_file.read_text() == "# Already exists"

    def test_overwrite_flag(self):
        """Test --overwrite flag forces file replacement."""
        html_file = self.input_dir / "test.html"
        html_file.write_text("<h1>New Content</h1>")

        output_file = self.output_dir / "test.md"
        output_file.write_text("# Old Content")

        result = subprocess.run(
            [sys.executable, str(BATCH_SCRIPT),
             "-d", str(self.input_dir), "-o", str(self.output_dir),
             "--overwrite"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Content should be overwritten
        assert "New Content" in output_file.read_text() or "New" in output_file.read_text()


def run_tests():
    """Run all tests and return exit code."""
    import shutil

    # Check pytest availability
    if shutil.which("pytest"):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", __file__, "-v"],
            cwd=Path(__file__).parent
        )
        return result.returncode

    # Fallback: run directly without pytest
    print("pytest not found, running basic tests...")
    print("=" * 60)

    test_classes = [
        TestDependencyCheck,
        TestConvertScript,
        TestBatchConvert,
        TestErrorHandling
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)
        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    if hasattr(instance, "setup_method"):
                        instance.setup_method()

                    getattr(instance, method_name)()

                    print(f"  ✓ {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  ✗ {method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    failed += 1
                finally:
                    if hasattr(instance, "teardown_method"):
                        try:
                            instance.teardown_method()
                        except:
                            pass

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
