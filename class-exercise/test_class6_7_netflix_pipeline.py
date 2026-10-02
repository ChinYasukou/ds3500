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

    def test_clean_text_normalizes_case_and_whitespace(self):
        utils = self.load_utils()
        self.assertTrue(
            hasattr(utils, "clean_text"),
            "clean_text has not been implemented",
        )

        result = utils.clean_text("  NOW   Here\tToday  ")

        self.assertEqual(result, "now here today")

    def test_remove_iqr_outliers_filters_values_outside_bounds(self):
        utils = self.load_utils()
        self.assertTrue(
            hasattr(utils, "remove_iqr_outliers"),
            "remove_iqr_outliers has not been implemented",
        )
        df = pd.DataFrame({"runtime_minutes": [10, 11, 12, 13, 100]})

        result = utils.remove_iqr_outliers(df, "runtime_minutes", 1.5)

        self.assertEqual(result["runtime_minutes"].tolist(), [10, 11, 12, 13])

    def test_remove_iqr_outliers_rejects_missing_column(self):
        utils = self.load_utils()
        self.assertTrue(
            hasattr(utils, "remove_iqr_outliers"),
            "remove_iqr_outliers has not been implemented",
        )
        df = pd.DataFrame({"title": ["A"]})

        with self.assertLogs("class6_7_netflix_utils", level="ERROR") as logs:
            with self.assertRaisesRegex(ValueError, "runtime_minutes"):
                utils.remove_iqr_outliers(df, "runtime_minutes", 1.5)

        self.assertIn("Column not found: runtime_minutes", logs.output[0])


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
                "title,type,country,runtime_minutes\n"
                " A ,Movie, US ,10\n"
                " A ,Movie, US ,10\n"
                "B,TV Show,Canada,11\n"
                "C,Movie,Japan,12\n"
                "D,Movie,France,13\n"
                "E,Movie,Spain,100\n"
                "F,Movie,Germany,\n",
                encoding="utf-8",
            )

            result = self.run_pipeline("--input", str(csv_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Loaded 7 rows and 4 columns", result.stderr)
        self.assertIn("Removed 1 duplicate row(s)", result.stderr)
        self.assertIn("Dropped 1 rows with missing values", result.stderr)
        self.assertIn("Removed 1 runtime_minutes outlier(s)", result.stderr)
        self.assertIn("Cleaned text column: title", result.stderr)
        self.assertIn("Cleaned text column: type", result.stderr)
        self.assertIn("Cleaned text column: country", result.stderr)
        self.assertIn("'rows_before': 7", result.stderr)
        self.assertIn("'rows_after': 4", result.stderr)
        self.assertIn("'rows_removed': 3", result.stderr)
        self.assertIn("'columns': 4", result.stderr)

    def test_verbose_mode_includes_utility_debug_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "netflix.csv"
            csv_path.write_text(
                "title,type,country,runtime_minutes\nA,Movie,US,90\n",
                encoding="utf-8",
            )

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
