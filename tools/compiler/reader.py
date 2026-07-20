"""Data reader and validation module for The Healthstream static site builder.

This module provides functions to safely load and validate JSON files representing
systems biology content nodes, glossary definitions, translations, and backlog items.
"""

import json
import os
from typing import Any, Dict, List
from .utils import load_json_file


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
        "epistemic_rating": dict,
        "tags": list,
        "reading_modes": dict,
        "edges": list,
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

    # Validate epistemic rating
    er = node_data["epistemic_rating"]
    for er_key, er_type in [("grade", str), ("rationale", str), ("debate_sides", list)]:
        if er_key not in er:
            raise ValueError(f"Validation Error in {file_path}: Missing required field 'epistemic_rating.{er_key}'")
        if not isinstance(er[er_key], er_type):
            raise ValueError(
                f"Validation Error in {file_path}: Field 'epistemic_rating.{er_key}' must be of type {er_type.__name__}"
            )

    valid_grades = {"High", "Moderate", "Low", "Very Low"}
    if er["grade"] not in valid_grades:
        raise ValueError(
            f"Validation Error in {file_path}: Invalid GRADE level '{er['grade']}'. Valid levels: {valid_grades}"
        )

    for idx, side in enumerate(er["debate_sides"]):
        if not isinstance(side, dict):
            raise ValueError(f"Validation Error in {file_path}: epistemic_rating.debate_sides[{idx}] must be an object")
        for sub_key in ["position", "arguments"]:
            if sub_key not in side:
                raise ValueError(
                    f"Validation Error in {file_path}: Missing field '{sub_key}' in epistemic_rating.debate_sides[{idx}]"
                )
            if not isinstance(side[sub_key], str):
                raise ValueError(
                    f"Validation Error in {file_path}: Field '{sub_key}' in epistemic_rating.debate_sides[{idx}] must be a string"
                )

    # Validate reading modes
    rm = node_data["reading_modes"]
    for rm_key, rm_type in [("overview_3min", str), ("deep_dive", list)]:
        if rm_key not in rm:
            raise ValueError(f"Validation Error in {file_path}: Missing required field 'reading_modes.{rm_key}'")
        if not isinstance(rm[rm_key], rm_type):
            raise ValueError(
                f"Validation Error in {file_path}: Field 'reading_modes.{rm_key}' must be of type {rm_type.__name__}"
            )

    for idx, item in enumerate(rm["deep_dive"]):
        if not isinstance(item, dict):
            raise ValueError(f"Validation Error in {file_path}: reading_modes.deep_dive[{idx}] must be an object")
        for sub_key in ["heading", "body"]:
            if sub_key not in item:
                raise ValueError(
                    f"Validation Error in {file_path}: Missing field '{sub_key}' in reading_modes.deep_dive[{idx}]"
                )
            if not isinstance(item[sub_key], str):
                raise ValueError(
                    f"Validation Error in {file_path}: Field '{sub_key}' in reading_modes.deep_dive[{idx}] must be a string"
                )

    # Validate edges
    for idx, edge in enumerate(node_data["edges"]):
        if not isinstance(edge, dict):
            raise ValueError(f"Validation Error in {file_path}: edges[{idx}] must be an object")
        for sub_key in ["target", "type", "mechanism"]:
            if sub_key not in edge:
                raise ValueError(
                    f"Validation Error in {file_path}: Missing field '{sub_key}' in edges[{idx}]"
                )
            if not isinstance(edge[sub_key], str):
                raise ValueError(
                    f"Validation Error in {file_path}: Field '{sub_key}' in edges[{idx}] must be a string"
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


def validate_backlog_item(item_data: Dict[str, Any], item_id: str = "") -> None:
    """Validates that a backlog item has all required fields including systems_analogy."""
    required_keys = ["id", "title", "description", "category", "systems_analogy"]
    target_id = item_id or item_data.get("id", "unknown")
    for key in required_keys:
        if key not in item_data or not item_data[key]:
            raise ValueError(f"Validation Error in Backlog Item '{target_id}': Missing required field '{key}'")
