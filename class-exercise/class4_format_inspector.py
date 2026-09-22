import json
import logging
import os
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def inspect_csv(filepath):
    """Read a CSV file and display basic information."""
    logger.info(f"Inspecting CSV: {filepath}")
    dataframe = pd.read_csv(filepath)
    print(dataframe.head(3))


def inspect_json(filepath):
    """Read a JSON file and display basic information."""
    logger.info(f"Inspecting JSON: {filepath}")
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)
    print(data)


def inspect_yaml(filepath):
    """Read a YAML file and display basic information."""
    logger.info(f"Inspecting YAML: {filepath}")
    with open(filepath, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    print(config)


def inspect_env():
    """Read a .env file and display basic information."""
    load_dotenv()
    keys = [
        key
        for key in ["USERNAME", "PASSWORD"]
        if os.getenv(key) is not None
    ]
    logger.info("Loaded environment variables from .env")
    print(keys)


def main():
    data_dir = Path("data")
    csv_path = data_dir / "sample.csv"
    json_path = data_dir / "sample.json"
    yaml_path = data_dir / "sample.yaml"

    inspect_csv(csv_path)
    inspect_json(json_path)
    inspect_yaml(yaml_path)
    inspect_env()


if __name__ == "__main__":
    main()
