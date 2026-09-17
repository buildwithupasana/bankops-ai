"""Exercise the terminal demonstration as a user would."""

from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parent / "bankops.py"


def test_demo_default_works_from_another_directory(tmp_path):
    result = subprocess.run([sys.executable, "-B", str(SCRIPT)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0
    assert "TXN001" in result.stdout
    assert "AED 2,500.00" in result.stdout
    assert "PROCESSING" in result.stdout


def test_demo_unknown_transaction():
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), "UNKNOWN"], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Transaction not found: UNKNOWN" in result.stderr
