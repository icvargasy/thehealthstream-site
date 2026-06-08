"""Data reader and validation module for The Healthstream static site builder.

This module provides functions to safely load and validate JSON files representing
systems biology content nodes, glossary definitions, translations, and backlog items.
"""

import json
import os
from typing import Any, Dict, List


def load_json_file(file_path: str) -> Any:
    """Loads a JSON file from the disk.

    Args:
        file_path: The absolute or relative string path to the JSON file.

    Returns:
        The parsed JSON representation (dict or list).

    Raises:
        FileNotFoundError: If the profile file is missing.
        ValueError: If the file content is invalid JSON.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"JSON file missing at: {file_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in file: {file_path}") from e


def validate_node(node_data: Dict[str, Any], file_path: str) -> None:
    """Validates the schema structure and values of an article content node.

    Args:
        node_data: The dictionary representation of the node JSON data.
        file_path: Filename or path context used for clear error reporting.

    Raises:
        ValueError: If any required key is missing or data types/values are invalid.
    """
    required_keys = {
        "type": str,
        "title": str,
        "hook_question": str,
        "takeaway_pill": str,
        "epistemic_status": str,
        "tags": list,
        "content": str,
        "evidence_table": list,
        "bibliography": list,
    }

    # Verify all keys exist and have correct types
    for key, expected_type in required_keys.items():
        if key not in node_data:
            raise ValueError(f"Validation Error in {file_path}: Missing required field '{key}'")
        if not isinstance(node_data[key], expected_type):
            raise ValueError(
                f"Validation Error in {file_path}: Field '{key}' must be of type {expected_type.__name__}"
            )

    # Validate categories
    valid_types = {"biology", "lifestyle", "book"}
    if node_data["type"] not in valid_types:
        raise ValueError(
            f"Validation Error in {file_path}: Invalid type '{node_data['type']}'. Valid types: {valid_types}"
        )

    # Validate epistemic status
    valid_status = {"consensus", "developing", "high-controversy"}
    if node_data["epistemic_status"] not in valid_status:
        raise ValueError(
            f"Validation Error in {file_path}: Invalid status '{node_data['epistemic_status']}'. "
            f"Valid statuses: {valid_status}"
        )

    # Validate evidence table elements
    for idx, item in enumerate(node_data["evidence_table"]):
        if not isinstance(item, dict):
            raise ValueError(f"Validation Error in {file_path}: evidence_table[{idx}] must be an object")
        for sub_key in ["study", "design", "sample", "outcome", "link"]:
            if sub_key not in item:
                raise ValueError(
                    f"Validation Error in {file_path}: Missing field '{sub_key}' in evidence_table[{idx}]"
                )
            if not isinstance(item[sub_key], str):
                raise ValueError(
                    f"Validation Error in {file_path}: Field '{sub_key}' in evidence_table[{idx}] must be a string"
                )

    # Validate bibliography elements
    for idx, item in enumerate(node_data["bibliography"]):
        if not isinstance(item, dict):
            raise ValueError(f"Validation Error in {file_path}: bibliography[{idx}] must be an object")
        for sub_key in ["id", "text", "link"]:
            if sub_key not in item:
                raise ValueError(
                    f"Validation Error in {file_path}: Missing field '{sub_key}' in bibliography[{idx}]"
                )
            if not isinstance(item[sub_key], str):
                raise ValueError(
                    f"Validation Error in {file_path}: Field '{sub_key}' in bibliography[{idx}] must be a string"
                )


def load_and_validate_all_nodes(nodes_dir: str) -> List[Dict[str, Any]]:
    """Crawls nodes directory and loads and validates all json article profiles.

    Args:
        nodes_dir: Path to directory containing source JSON nodes.

    Returns:
        A list of validated node dictionaries, each including a 'slug' field
        derived from the file name.

    Raises:
        FileNotFoundError: If nodes directory is missing.
    """
    if not os.path.isdir(nodes_dir):
        raise FileNotFoundError(f"Nodes source directory missing at: {nodes_dir}")

    nodes = []
    for entry in os.listdir(nodes_dir):
        if entry.endswith(".json"):
            file_path = os.path.join(nodes_dir, entry)
            node_data = load_json_file(file_path)
            validate_node(node_data, file_path)
            
            # Extract slug from the filename
            node_data["slug"] = os.path.splitext(entry)[0]
            nodes.append(node_data)
            
    return nodes
