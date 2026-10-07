import subprocess
import sys
import tempfile
import unittest
from importlib import import_module
from pathlib import Path

import pandas as pd


class Class8StarterTests(unittest.TestCase):
    def load_module(self, name):
        try:
            return import_module(name)
        except ModuleNotFoundError:
            self.fail(f"{name} has not been implemented")

    def test_load_netflix_reads_csv(self):
        loader = self.load_module("class8_data_loader")
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "netflix.csv"
            csv_path.write_text("title,type\nA,Movie\n", encoding="utf-8")

            result = loader.load_netflix(csv_path)

        self.assertEqual(result.to_dict("records"), [{"title": "A", "type": "Movie"}])

    def test_require_columns_returns_valid_dataframe(self):
        validator = self.load_module("class8_data_validator")
        df = pd.DataFrame({"title": ["A"], "type": ["Movie"]})

        result = validator.require_columns(df, ["title", "type"])

        self.assertIs(result, df)

    def test_require_columns_rejects_missing_columns(self):
        validator = self.load_module("class8_data_validator")
        df = pd.DataFrame({"title": ["A"]})

        with self.assertLogs("class8_data_validator", level="ERROR"):
            with self.assertRaisesRegex(ValueError, "type"):
                validator.require_columns(df, ["title", "type"])

    def test_pipeline_logs_each_completed_stage(self):
        script = Path(__file__).with_name("class8_pipeline.py")

        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=script.parent,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("class8_data_loader", result.stderr)
        self.assertIn("Data loaded", result.stderr)
        self.assertIn("class8_data_validator", result.stderr)
        self.assertIn("Validation completed", result.stderr)
        self.assertIn("__main__", result.stderr)
        self.assertIn("Pipeline completed", result.stderr)


if __name__ == "__main__":
    unittest.main()
