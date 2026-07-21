#!/usr/bin/env python3
"""Helper utilities for automated content pipeline curation and validation.

Supports programmatic backlog addition, non-interactive draft generation,
jargon bolding validation, vocabulary schema checks, and edge referential integrity checks.
Can be used both as a Python module and as a command-line interface (CLI).
"""

import argparse
import datetime
import os
import re
import sys
from typing import Any, Dict, List, Set, Tuple

# Ensure tools/ is in the python path for importing compiler modules
sys.path.insert(0, os.path.dirname(__file__))
from compiler.utils import slugify, load_json_file, save_json_file


def add_to_backlog(
    title: str, description: str, category: str, tags: List[str], votes: int = 0
) -> Dict[str, Any]:
    """Programmatically appends a new proposal to the pipeline backlog.

    Args:
        title: Title of the proposal.
        description: Description or curiosity question.
        category: Category (biology, lifestyle, book).
        tags: List of descriptive tags.
        votes: Starting votes count.

    Returns:
        The newly created backlog item dictionary.

    Raises:
        ValueError: If parameters are invalid, tag taxonomy check fails, or slug already exists.
    """
    src_dir = "src"
    backlog_path = os.path.join(src_dir, "backlog.json")
    
    if not title:
        raise ValueError("Title is required.")
    
    valid_categories = {"biology", "lifestyle", "book"}
    if category not in valid_categories:
        raise ValueError(f"Invalid category '{category}'. Valid: {valid_categories}")

    # Validate tags against tags.json
    tags_registry_path = os.path.join(src_dir, "tags.json")
    if os.path.exists(tags_registry_path):
        valid_tags = set(load_json_file(tags_registry_path).keys())
        invalid_tags = [t for t in tags if t not in valid_tags]
        if invalid_tags:
            raise ValueError(f"Non-standard tags: {invalid_tags}. Allowed tags: {sorted(list(valid_tags))}")

    slug = slugify(title)
    backlog = load_json_file(backlog_path, default_empty=[])
    
    if any(item["id"] == slug for item in backlog):
        raise ValueError(f"A proposal with ID '{slug}' already exists in the backlog.")

    new_item = {
        "id": slug,
        "title": title,
        "description": description or "Explore feedback loops and connectivity for this concept.",
        "category": category,
        "votes": votes,
        "tags": tags if tags is not None else [],
        "created_at": datetime.date.today().isoformat(),
    }
    
    backlog.append(new_item)
    save_json_file(backlog_path, backlog)
    return new_item


def bootstrap_draft(slug: str) -> str:
    """Bootstraps a schema-compliant content node draft from backlog.

    Reads from backlog, creates template, and pops the item from the backlog.

    Args:
        slug: The unique identifier slug of the backlog item.

    Returns:
        The absolute path to the generated draft file.

    Raises:
        ValueError: If slug is not found in the backlog.
    """
    src_dir = "src"
    backlog_path = os.path.join(src_dir, "backlog.json")
    drafts_dir = os.path.join(src_dir, "nodes", "en", "drafts")
    
    backlog = load_json_file(backlog_path)
    selected_item = next((item for item in backlog if item["id"] == slug), None)
    
    if not selected_item:
        raise ValueError(f"No backlog item found with ID '{slug}'.")

    title = selected_item["title"]
    category = selected_item["category"]
    description = selected_item["description"]

    node_data = {
        "type": category,
        "title": title,
        "hook_question": description,
        "metadata": {
            "created_at": selected_item.get("created_at", datetime.date.today().isoformat()),
            "last_audited": datetime.date.today().isoformat(),
            "audit_history": [
                {
                    "date": datetime.date.today().isoformat(),
                    "grade_assigned": "Low",
                    "summary": "Initial draft bootstrapper template creation."
                }
            ]
        },
        "takeaway_pill": "1-Min takeaway summary based on evidence (Actionable and direct).",
        "epistemic_rating": {
            "grade": "Low",
            "rationale": "GRADE-based evaluation summary of supporting literature.",
            "debate_sides": [
                {
                    "position": "Brief statement of Hypothesis A.",
                    "arguments": "Supporting data / trials."
                }
            ]
        },
        "tags": selected_item.get("tags") or [],
        "reading_modes": {
            "overview_3min": "A 3-min narrative overview mapping the biological feedback loops. Use bold `**` tags for glossary terms.",
            "deep_dive": [
                {
                    "heading": "Molecular Feedback Loops",
                    "body": "Detailed biochemical steps (use bold `**` for vocabulary terms)."
                }
            ]
        },
        "edges": [
            {
                "target": "target-slug-goes-here",
                "type": "activates",
                "mechanism": "How this node influences the target node."
            }
        ],
        "evidence_table": [
            {
                "study": "Author et al., Year",
                "design": "Study design (e.g., RCT, in vivo)",
                "sample": "Cohort description (e.g., n=40 adults)",
                "outcome": "Specific outcome data.",
                "link": "https://pubmed.ncbi.nlm.nih.gov/XXXXX/"
            }
        ],
        "bibliography": [
            {
                "id": "ref1",
                "text": "Full Vancouver-style citation.",
                "link": "Direct DOI or publisher link."
            }
        ]
    }

    os.makedirs(drafts_dir, exist_ok=True)
    target_file = os.path.join(drafts_dir, f"{slug}.json")
    save_json_file(target_file, node_data)

    # Remove item from backlog
    backlog = [item for item in backlog if item["id"] != slug]
    save_json_file(backlog_path, backlog)

    return os.path.abspath(target_file)


def validate_jargon_bolding(draft_path: str) -> Tuple[List[str], List[str]]:
    """Validates jargon word bolding patterns against vocabulary.json.

    Identifies:
    1. Bolded terms (`**term**`) in draft text that are NOT keys in vocabulary.json.
    2. Terms in vocabulary.json that exist in draft text but are NOT bolded.

    Args:
        draft_path: Path to the content node draft.

    Returns:
        A tuple of (unmapped_bolded_terms, missing_bold_terms).
    """
    src_dir = "src"
    vocab_path = os.path.join(src_dir, "vocabulary.json")
    
    vocab = load_json_file(vocab_path)
    # Get all lowercase vocabulary keys for case-insensitive matching
    vocab_keys_lower = {key.lower(): key for key in vocab.keys()}
    
    draft = load_json_file(draft_path)
    
    # Concatenate all text fields to search
    text_blocks = []
    text_blocks.append(draft.get("takeaway_pill", ""))
    rm = draft.get("reading_modes", {})
    text_blocks.append(rm.get("overview_3min", ""))
    for section in rm.get("deep_dive", []):
        text_blocks.append(section.get("heading", ""))
        text_blocks.append(section.get("body", ""))
        
    full_text = " ".join(text_blocks)

    # Find all bolded phrases: e.g. **AMPK**
    bolded_phrases = re.findall(r"\*\*([^*]+)\*\*", full_text)
    unmapped_bolded = []
    for phrase in bolded_phrases:
        phrase_clean = phrase.strip()
        if phrase_clean.lower() not in vocab_keys_lower:
            unmapped_bolded.append(phrase_clean)

    # Find all instances of vocabulary terms in text that are NOT bolded
    missing_bold = []
    # Tokenize full text into words, removing asterisks to look for unbolded matches
    text_no_asterisks = full_text.replace("**", " ")
    for canonical_key in vocab.keys():
        # Search for exact word matches using word boundaries
        pattern = r"\b" + re.escape(canonical_key) + r"\b"
        if re.search(pattern, text_no_asterisks, re.IGNORECASE):
            # Check if this exact term is bolded in the original text
            bold_pattern = r"\*\*" + re.escape(canonical_key) + r"\*\*"
            if not re.search(bold_pattern, full_text, re.IGNORECASE):
                missing_bold.append(canonical_key)

    return list(set(unmapped_bolded)), list(set(missing_bold))


def validate_node_tags(draft_path: str) -> List[str]:
    """Checks draft tags against the standardized taxonomy lexicon.

    Args:
        draft_path: Path to the draft JSON node.

    Returns:
        A list of non-standard tags.
    """
    try:
        src_dir = "src"
        tags_path = os.path.join(src_dir, "tags.json")
        if os.path.exists(tags_path):
            tags_registry = load_json_file(tags_path)
            valid_tags = set(tags_registry.keys())
        else:
            valid_tags = set()

        draft = load_json_file(draft_path)
        tags = draft.get("tags") or []
        non_standard = []
        for tag in tags:
            tag_clean = tag.strip().lower()
            if tag_clean not in valid_tags:
                non_standard.append(tag)
        return non_standard
    except Exception:
        return []


def validate_edge_targets(draft_path: str) -> List[str]:
    """Validates that all target slugs in edges exist.

    Checks if they exist under active nodes (src/nodes/en/) or the backlog.

    Args:
        draft_path: Path to the content node draft.

    Returns:
        A list of unresolved target slugs.
    """
    src_dir = "src"
    nodes_dir = os.path.join(src_dir, "nodes", "en")
    backlog_path = os.path.join(src_dir, "backlog.json")
    
    draft = load_json_file(draft_path)
    edges = draft.get("edges", [])
    if not edges:
        return []

    # Gather all existing slugs
    existing_slugs: Set[str] = set()
    if os.path.exists(nodes_dir):
        for entry in os.listdir(nodes_dir):
            if entry.endswith(".json"):
                existing_slugs.add(os.path.splitext(entry)[0])
                
    if os.path.exists(backlog_path):
        backlog = load_json_file(backlog_path)
        for item in backlog:
            existing_slugs.add(item["id"])

    # Include the current node slug (derived from file name)
    current_slug = os.path.splitext(os.path.basename(draft_path))[0]
    existing_slugs.add(current_slug)

    unresolved = []
    for edge in edges:
        target = edge.get("target", "")
        # Skip placeholders
        if "goes-here" in target or not target:
            unresolved.append(target)
            continue
        if target not in existing_slugs:
            unresolved.append(target)

    return unresolved


def validate_vocabulary_schema(vocab_path: str) -> List[str]:
    """Validates the schema structures of all entries in vocabulary.json.

    Args:
        vocab_path: Path to vocabulary.json.

    Returns:
        A list of string error messages detailing schema breaches.
    """
    errors = []
    if not os.path.exists(vocab_path):
        errors.append(f"Vocabulary file missing at: {vocab_path}")
        return errors

    try:
        vocab = load_json_file(vocab_path)
    except Exception as e:
        errors.append(f"Failed parsing vocabulary.json: {e}")
        return errors

    valid_taxonomies = {"protein", "molecule", "process", "concept", "organism", "condition", "framework"}
    valid_statuses = {"verified_human", "verified_agent_grounded", "ai_generated"}

    for term, item in vocab.items():
        if not isinstance(item, dict):
            errors.append(f"Term '{term}' must map to an object, got {type(item).__name__}")
            continue

        # Check required fields
        if "definition" not in item or not isinstance(item["definition"], str) or not item["definition"].strip():
            errors.append(f"Term '{term}': Missing or empty 'definition' string.")
        
        if "vulgarized_analogy" not in item or not isinstance(item["vulgarized_analogy"], str) or not item["vulgarized_analogy"].strip():
            errors.append(f"Term '{term}': Missing or empty 'vulgarized_analogy' string.")

        if "taxonomy" not in item or item["taxonomy"] not in valid_taxonomies:
            errors.append(f"Term '{term}': Invalid or missing 'taxonomy'. Must be one of {valid_taxonomies}")

        if "verification_status" not in item or item["verification_status"] not in valid_statuses:
            errors.append(f"Term '{term}': Invalid or missing 'verification_status'. Must be one of {valid_statuses}")

        if "citations" not in item or not isinstance(item["citations"], list):
            errors.append(f"Term '{term}': Missing or invalid 'citations' list.")
        else:
            for idx, citation in enumerate(item["citations"]):
                if not isinstance(citation, dict):
                    errors.append(f"Term '{term}': Citation[{idx}] must be an object.")
                    continue
                for sub_key in ["text", "link", "defining_quote"]:
                    if sub_key not in citation or not isinstance(citation[sub_key], str) or not citation[sub_key].strip():
                        errors.append(f"Term '{term}': Citation[{idx}] missing or empty '{sub_key}' string.")
                if "quote_page" in citation and not isinstance(citation["quote_page"], str):
                    errors.append(f"Term '{term}': Citation[{idx}] field 'quote_page' must be a string.")

    return errors


def main() -> None:
    """CLI routing entry point."""
    parser = argparse.ArgumentParser(
        description="Helper CLI for automated/manual content pipeline curation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # subcommand: add-backlog
    add_parser = subparsers.add_parser("add-backlog", help="Manually add a proposal to the backlog.")
    add_parser.add_argument("--title", required=True, help="Title of the proposal.")
    add_parser.add_argument("--desc", default="", help="Description or curiosity question.")
    add_parser.add_argument(
        "--cat",
        required=True,
        choices=["biology", "lifestyle", "book"],
        help="Category of the proposal.",
    )
    add_parser.add_argument("--tags", default="", help="Comma-separated tags list.")
    add_parser.add_argument("--votes", type=int, default=0, help="Initial votes count.")

    # subcommand: bootstrap-draft
    bootstrap_parser = subparsers.add_parser(
        "bootstrap-draft", help="Bootstrap a content node draft from the backlog."
    )
    bootstrap_parser.add_argument(
        "--slug", required=True, help="The slug identifier of the backlog item."
    )

    # subcommand: validate
    validate_parser = subparsers.add_parser(
        "validate", help="Validate a draft content node's jargon and edges, and check vocabulary.json."
    )
    validate_parser.add_argument("file_path", help="Path to the JSON draft content node.")

    args = parser.parse_args()

    try:
        if args.command == "add-backlog":
            tags_list = [t.strip().lower() for t in args.tags.split(",") if t.strip()]
            new_item = add_to_backlog(
                args.title, args.desc, args.cat, tags_list, args.votes
            )
            print(f"[Success] Added to backlog: {new_item['id']} ({new_item['category']})")

        elif args.command == "bootstrap-draft":
            draft_path = bootstrap_draft(args.slug)
            print(f"[Success] Draft generated successfully at: {draft_path}")

        elif args.command == "validate":
            if not os.path.exists(args.file_path):
                print(f"[Error] File not found: {args.file_path}")
                sys.exit(1)
                
            unmapped_bolded, missing_bold = validate_jargon_bolding(args.file_path)
            unresolved_edges = validate_edge_targets(args.file_path)
            non_standard_tags = validate_node_tags(args.file_path)
            
            # Also run vocabulary check automatically
            src_dir = "src"
            vocab_path = os.path.join(src_dir, "vocabulary.json")
            vocab_errors = validate_vocabulary_schema(vocab_path)
            
            error_found = False
            
            print(f"=== Validation Report: {os.path.basename(args.file_path)} ===")
            if unmapped_bolded:
                print("\n[Warning] Bolded terms NOT defined in vocabulary.json:")
                for term in unmapped_bolded:
                    print(f"  - {term}")
            else:
                print("\n[Pass] All bolded terms are mapped in vocabulary.json.")

            if missing_bold:
                print("\n[Warning] Vocabulary terms found in text but NOT bolded:")
                for term in missing_bold:
                    print(f"  - {term}")
            else:
                print("\n[Pass] All vocabulary terms found in text are correctly bolded.")

            if non_standard_tags:
                print("\n[Warning] Non-standard tags detected (not in standard taxonomy):")
                for tag in non_standard_tags:
                    print(f"  - {tag}")
                try:
                    tags_registry = load_json_file(os.path.join("src", "tags.json"))
                    print(f"  * Standard Taxonomy: {sorted(list(tags_registry.keys()))}")
                except Exception:
                    pass
            else:
                print("\n[Pass] All tags adhere to standard taxonomy.")

            if unresolved_edges:
                print("\n[Error] Unresolved target slugs in edges:")
                for target in unresolved_edges:
                    print(f"  - {target}")
                error_found = True
            else:
                print("\n[Pass] All edge targets resolved to active nodes or backlog items.")
                
            print("\n=== Vocabulary Schema Validation ===")
            if vocab_errors:
                print(f"\n[Error] Found {len(vocab_errors)} errors in vocabulary.json:")
                for err in vocab_errors:
                    print(f"  - {err}")
                error_found = True
            else:
                print("\n[Pass] vocabulary.json schema is fully compliant.")
                
            print("\n=========================================")
            if error_found:
                print("Validation Status: FAILED (Errors detected)")
                sys.exit(1)
            else:
                print("Validation Status: PASSED (Warnings may apply)")
                sys.exit(0)

    except Exception as e:
        print(f"[Error] Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
