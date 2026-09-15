import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
SCRIPT = ROOT / "class2_data_checker.py"
STUDENTS = ROOT / "students.csv"


def run_checker(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class DataCheckerTests(unittest.TestCase):
    def test_default_report_and_info_logging(self):
        report = ROOT / "data_quality.txt"
        report.unlink(missing_ok=True)

        result = run_checker("--input", str(STUDENTS))

        self.assertEqual(result.returncode, 0)
        self.assertIn("INFO", result.stderr)
        self.assertIn("File validated", result.stderr)
        self.assertIn("Loaded 5 rows", result.stderr)
        self.assertIn("WARNING", result.stderr)
        self.assertIn("Row 4 has missing values", result.stderr)
        self.assertIn("Row 6 has missing values", result.stderr)
        self.assertEqual(
            report.read_text(),
            "Number of rows: 5\n"
            "Number of columns: 3\n"
            "Number of rows with missing values: 2\n",
        )

    def test_verbose_enables_debug_logging(self):
        result = run_checker("--input", str(STUDENTS), "--verbose")

        self.assertEqual(result.returncode, 0)
        self.assertIn("DEBUG", result.stderr)
        self.assertIn("Arguments parsed: filename=", result.stderr)
        self.assertIn("Loading data from:", result.stderr)

    def test_missing_file_exits_with_error(self):
        result = run_checker("--input", "missing.csv")

        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR", result.stderr)
        self.assertIn("File not found: 'missing.csv'", result.stderr)


if __name__ == "__main__":
    unittest.main()
