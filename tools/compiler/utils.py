"""Shared utility functions for The Healthstream compilation pipeline."""

import json
import os
import re
from typing import Any


def slugify(text: str) -> str:
    """Converts a raw title string into a url-safe slug.

    Args:
        text: Raw text string.

    Returns:
        A lowercase slug with non-alphanumeric characters replaced by hyphens.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def load_json_file(file_path: str, default_empty: Any = None) -> Any:
    """Loads a JSON file from disk.

    Args:
        file_path: The path to the JSON file.
        default_empty: If set, returns this value if file is missing (e.g. [] or {}),
                      otherwise raises FileNotFoundError.

    Returns:
        The parsed JSON representation.

    Raises:
        FileNotFoundError: If the file is missing and default_empty is None.
        ValueError: If the file contains invalid JSON.
        RuntimeError: If reading fails due to other system errors.
    """
    if not os.path.exists(file_path):
        if default_empty is not None:
            return default_empty
        raise FileNotFoundError(f"JSON file missing at: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in file: {file_path}") from e
    except Exception as e:
        raise RuntimeError(f"Error reading JSON file at {file_path}: {e}") from e


def save_json_file(file_path: str, data: Any) -> None:
    """Saves data to a JSON file safely with UTF-8 encoding.

    Args:
        file_path: Path to write the JSON file.
        data: Data to serialize.

    Raises:
        RuntimeError: If writing to the file fails.
    """
    try:
        dir_name = os.path.dirname(os.path.abspath(file_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        raise RuntimeError(f"Error saving JSON to {file_path}: {e}") from e
