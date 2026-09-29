import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from importlib import import_module
from io import StringIO
from pathlib import Path

import pandas as pd


class NetflixUtilsTests(unittest.TestCase):
    def load_utils(self):
        try:
            return import_module("class6_7_netflix_utils")
        except ModuleNotFoundError:
            self.fail("class6_7_netflix_utils.py has not been implemented")

    def test_show_overview_prints_required_details(self):
        utils = self.load_utils()
        df = pd.DataFrame({"title": ["Example"], "release_year": [2022]})
        output = StringIO()

        with redirect_stdout(output):
            utils.show_overview(df)

        text = output.getvalue()
        self.assertIn("Shape: (1, 2)", text)
        self.assertIn("Columns:", text)
        self.assertIn("Data types:", text)
        self.assertIn("Example", text)

    def test_remove_duplicates_returns_unique_rows(self):
        utils = self.load_utils()
        df = pd.DataFrame({"title": ["A", "A", "B"]})

        result = utils.remove_duplicates(df)

        self.assertEqual(result["title"].tolist(), ["A", "B"])

    def test_drop_missing_rows_removes_any_incomplete_row(self):
        utils = self.load_utils()
        df = pd.DataFrame({"title": ["A", "B"], "score": [90, None]})

        result = utils.drop_missing_rows(df)

        self.assertEqual(result["title"].tolist(), ["A"])


class NetflixPipelineTests(unittest.TestCase):
    def run_pipeline(self, *args):
        script = Path(__file__).with_name("class6_7_netflix_pipeline.py")
        return subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_pipeline_reports_cleaning_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "netflix.csv"
            csv_path.write_text(
                "title,type,score\nA,Movie,90\nA,Movie,90\nB,Movie,\n",
                encoding="utf-8",
            )

            result = self.run_pipeline("--input", str(csv_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Loaded 3 rows and 3 columns", result.stderr)
        self.assertIn("Removed 1 duplicate row(s)", result.stderr)
        self.assertIn("Dropped 1 rows with missing values", result.stderr)

    def test_verbose_mode_includes_utility_debug_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "netflix.csv"
            csv_path.write_text("title,type\nA,Movie\n", encoding="utf-8")

            result = self.run_pipeline("--verbose", "--input", str(csv_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DEBUG", result.stderr)
        self.assertIn("class6_7_netflix_utils", result.stderr)

    def test_missing_input_exits_with_error(self):
        result = self.run_pipeline("--input", "data/missing.csv")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Input file not found: data/missing.csv", result.stderr)


if __name__ == "__main__":
    unittest.main()
