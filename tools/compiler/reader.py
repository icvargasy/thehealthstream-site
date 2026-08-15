"""Data reader and validation module for The Healthstream static site builder.

This module provides functions to safely load and validate JSON files representing
systems biology content nodes, glossary definitions, translations, and backlog items.
"""

import json
import os
import re
from typing import Any, Dict, List, Set
from .utils import load_json_file

BARE_ACTION_VERB_REGEX = re.compile(
    r"^(Restructures|Regulates|Activates|Clears|Triggers|Modulates|Prevents|Reduces|Enhances|Improves|Accelerates|Drives|Inhibits|Promotes|Suppresses|Alters)\b",
    re.IGNORECASE,
)


def validate_systems_analogy(analogy: str, context: str) -> None:
    """Validates that a systems analogy complies with the universal Systems Analogy Protocol.

    Enforces:
        1. Single sentence length constraint (<= 25 words).
        2. Concrete noun subject (must not start with a bare action verb).

    Args:
        analogy: The analogy string to validate.
        context: Description of the calling source (file, term, or item ID).

    Raises:
        ValueError: If the analogy violates length or grammatical subject constraints.
    """
    if not analogy or not isinstance(analogy, str):
        return
    text = analogy.strip()
    words = text.split()
    if len(words) > 25:
        raise ValueError(
            f"Validation Error in {context}: Systems analogy exceeds universal 25-word ceiling ({len(words)} words): '{text}'"
        )
    match_verb = BARE_ACTION_VERB_REGEX.match(text)
    if match_verb:
        raise ValueError(
            f"Validation Error in {context}: Systems analogy must start with a concrete noun subject, not bare action verb '{match_verb.group(0)}': '{text}'"
        )

# Lazily cached tag allowlist — populated on first validation call.
_VALID_TAGS_CACHE: Set[str] = set()


def _load_valid_tags() -> Set[str]:
    """Loads the valid tag set from src/tags.json.

    Searches upward from this file to locate tags.json so the validator works
    regardless of the working directory. Falls back to a hardcoded minimal set
    if the file cannot be found (e.g. in isolated unit tests).

    Returns:
        A set of lowercase tag strings that are considered valid.
    """
    global _VALID_TAGS_CACHE
    if _VALID_TAGS_CACHE:
        return _VALID_TAGS_CACHE

    # Walk up to find tags.json relative to this file
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "..", "..", "src", "tags.json")
    candidate = os.path.normpath(candidate)
    if os.path.isfile(candidate):
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                tags_data = json.load(f)
            _VALID_TAGS_CACHE = {k.lower() for k in tags_data.keys()}
            return _VALID_TAGS_CACHE
        except (json.JSONDecodeError, OSError):
            pass

    # Fallback — keeps existing nodes valid if tags.json is unreachable
    _VALID_TAGS_CACHE = {
        "biology", "lifestyle", "book", "longevity", "metabolism",
        "circadian", "sleep", "exercise", "fasting", "mitochondria",
        "supplements", "fgf21",
    }
    return _VALID_TAGS_CACHE


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

    # Validate tag entries against the authoritative tags.json registry
    valid_tags = _load_valid_tags()
    for t in node_data["tags"]:
        if not isinstance(t, str) or t.lower() not in valid_tags:
            raise ValueError(f"Validation Error in {file_path}: Unregistered or invalid tag '{t}'. Valid tags: {valid_tags}")

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

    valid_stances = {"supporting", "counter", "nuanced"}
    for idx, side in enumerate(er["debate_sides"]):
        if not isinstance(side, dict):
            raise ValueError(f"Validation Error in {file_path}: epistemic_rating.debate_sides[{idx}] must be an object")
        for sub_key in ["position", "arguments", "stance", "citations"]:
            if sub_key not in side:
                raise ValueError(
                    f"Validation Error in {file_path}: Missing field '{sub_key}' in epistemic_rating.debate_sides[{idx}]"
                )
        if not isinstance(side["position"], str) or not isinstance(side["arguments"], str):
            raise ValueError(
                f"Validation Error in {file_path}: 'position' and 'arguments' in epistemic_rating.debate_sides[{idx}] must be strings"
            )
        if not isinstance(side["stance"], str) or side["stance"].lower().strip() not in valid_stances:
            raise ValueError(
                f"Validation Error in {file_path}: Invalid stance '{side['stance']}' in epistemic_rating.debate_sides[{idx}]. Valid stances: {valid_stances}"
            )
        if not isinstance(side["citations"], list) or not all(isinstance(c, str) for c in side["citations"]):
            raise ValueError(
                f"Validation Error in {file_path}: Field 'citations' in epistemic_rating.debate_sides[{idx}] must be a list of strings"
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

    # Validate edges or related_circuits
    if "related_circuits" not in node_data and "edges" not in node_data:
        raise ValueError(f"Validation Error in {file_path}: Missing required field 'related_circuits' or 'edges'")

    if "edges" not in node_data:
        node_data["edges"] = []

    if node_data["edges"]:
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

    if "related_circuits" in node_data:
        rc = node_data["related_circuits"]
        if not isinstance(rc, dict):
            raise ValueError(f"Validation Error in {file_path}: Field 'related_circuits' must be an object")
        for dir_key in ("upstream", "downstream", "similar"):
            if dir_key in rc:
                if not isinstance(rc[dir_key], list):
                    raise ValueError(f"Validation Error in {file_path}: Field 'related_circuits.{dir_key}' must be a list")

    # Validate optional or recommended fields
    systems_analogy = node_data.get("systems_analogy_hook", "")
    if systems_analogy:
        validate_systems_analogy(systems_analogy, file_path)

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
        for sub_key in ["id", "text", "link", "tag"]:
            if sub_key not in item:
                raise ValueError(
                    f"Validation Error in {file_path}: Missing field '{sub_key}' in bibliography[{idx}]"
                )
            if not isinstance(item[sub_key], str) or not item[sub_key].strip():
                raise ValueError(
                    f"Validation Error in {file_path}: Field '{sub_key}' in bibliography[{idx}] must be a non-empty string"
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
    for entry in sorted(os.listdir(nodes_dir)):
        file_path = os.path.join(nodes_dir, entry)
        if os.path.isfile(file_path) and entry.endswith(".json"):
            node_data = load_json_file(file_path)
            validate_node(node_data, file_path)
            
            # Extract slug from the filename
            node_data["slug"] = os.path.splitext(entry)[0]
            nodes.append(node_data)
            
    return nodes


def validate_backlog_item(item_data: Dict[str, Any], item_id: str = "") -> None:
    """Validates that a backlog item has all required fields including systems_analogy and grade."""
    required_keys = ["id", "title", "hook_question", "description", "category", "systems_analogy", "grade"]
    target_id = item_id or item_data.get("id", "unknown")
    for key in required_keys:
        if key not in item_data:
            raise ValueError(f"Validation Error in Backlog Item '{target_id}': Missing required field '{key}'")
        val = item_data[key]
        if val is None or (isinstance(val, str) and not val.strip()):
            raise ValueError(f"Validation Error in Backlog Item '{target_id}': Empty required field '{key}'")

    validate_systems_analogy(item_data["systems_analogy"], f"Backlog Item '{target_id}'")

    valid_grades = {"High", "Moderate", "Low", "Very Low"}
    if item_data["grade"] not in valid_grades:
        raise ValueError(
            f"Validation Error in Backlog Item '{target_id}': Invalid grade '{item_data['grade']}'. Valid levels: {valid_grades}"
        )

    if "tags" in item_data and isinstance(item_data["tags"], list):
        valid_tags = _load_valid_tags()
        for t in item_data["tags"]:
            if not isinstance(t, str) or t.lower() not in valid_tags:
                raise ValueError(f"Validation Error in Backlog Item '{target_id}': Unregistered or invalid tag '{t}'. Valid tags: {valid_tags}")



def validate_vocabulary_item(item_data: Dict[str, Any], term: str) -> None:
    """Validates vocabulary entry fields and enforces 'verification_status: ai_generated' default.

    Args:
        item_data: Dictionary representing term definition properties.
        term: Term string key for context reporting.
    """
    if not isinstance(item_data, dict):
        raise ValueError(f"Validation Error in Vocabulary term '{term}': Entry must be a JSON object")

    vulgarized_analogy = item_data.get("vulgarized_analogy", "")
    if vulgarized_analogy:
        validate_systems_analogy(vulgarized_analogy, f"Vocabulary term '{term}'")

    status = item_data.get("verification_status")
    if not status or status not in {"verified_human", "ai_generated"}:
        item_data["verification_status"] = "ai_generated"

